"""Free local image generation on NVIDIA GPUs; optional dependencies."""
from __future__ import annotations
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
MODEL_ID = 'Lykon/absolute-reality-1.81'
REVISION = '569d201654dca1426f1e090fca3953acc7db2c30'
MODEL_DIR = ROOT / 'models/absolute-reality-1.81'
MODEL_FILES = ['README.md', 'model_index.json', 'feature_extractor/preprocessor_config.json',
               'safety_checker/config.json', 'safety_checker/model.fp16.safetensors',
               'scheduler/scheduler_config.json', 'text_encoder/config.json', 'text_encoder/model.fp16.safetensors',
               'tokenizer/merges.txt', 'tokenizer/special_tokens_map.json', 'tokenizer/tokenizer_config.json',
               'tokenizer/vocab.json', 'unet/config.json', 'unet/diffusion_pytorch_model.fp16.safetensors',
               'vae/config.json', 'vae/diffusion_pytorch_model.fp16.safetensors']
NEGATIVE = ('cartoon, anime, illustration, painting, plastic, blurry, low quality, '
            'watermark, logo, text, letters, malformed objects, distorted perspective')


def download_model():
    import studio
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for filename in MODEL_FILES:
        path = MODEL_DIR / filename
        if path.is_file():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f'https://huggingface.co/{MODEL_ID}/resolve/{REVISION}/{filename}'
        print(f'Baixando modelo: {filename}', flush=True)
        request = urllib.request.Request(url, headers={'User-Agent': 'LocalVideoStudio/0.3'})
        temporary = path.with_name(path.name + '.part')
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open('wb') as output:
            expected = int(response.headers.get('Content-Length', 0))
            size = 0
            while block := response.read(8 * 1024 * 1024):
                output.write(block)
                size += len(block)
        if expected and size != expected:
            raise ValueError(f'Download incompleto: {filename}. Execute novamente.')
        temporary.replace(path)
    studio.write(MODEL_DIR / 'provenance.json', {'model': MODEL_ID, 'revision': REVISION,
        'license': 'CreativeML Open RAIL-M', 'source': f'https://huggingface.co/{MODEL_ID}',
        'files': {name: studio.file_hash(MODEL_DIR / name) for name in MODEL_FILES}})
    print(f'Modelo disponível: {MODEL_DIR}', flush=True)


def build_prompt(scene):
    subject = scene.get('image_prompt') or scene.get('visual_query')
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError('A cena precisa de image_prompt ou visual_query em inglês.')
    return ('Photorealistic documentary still, natural light, 35mm lens. ' + subject.strip() +
            '. No text or logos.')


def generate(path, selected_scene=None, seed=42, steps=28, append=False):
    import studio
    data = studio.read(path)
    if selected_scene is not None and not 1 <= selected_scene <= len(data['scenes']):
        raise ValueError('Número de cena inválido.')
    if not 8 <= steps <= 60 or not 0 <= seed <= 2**32 - 1:
        raise ValueError('Use 8–60 passos e seed entre 0 e 4294967295.')
    pending = [(index, scene, build_prompt(scene)) for index, scene in enumerate(data['scenes'], 1)
               if (selected_scene is None or selected_scene == index)
               and not any(s.get('synthetic') for s in studio.scene_assets(scene))
               and (append or not studio.scene_assets(scene))]
    if not pending:
        raise ValueError('Nenhuma cena elegível. Use --append para adicionar IA aos materiais existentes.')
    missing = [name for name in MODEL_FILES if not (MODEL_DIR / name).is_file()]
    if missing:
        raise ValueError('Modelo local ausente. Execute setup-ai.ps1 primeiro (download inicial de alguns GB).')
    try:
        import torch
        from diffusers import StableDiffusionPipeline, DEISMultistepScheduler
    except ImportError as exc:
        raise ValueError('Dependências de IA ausentes. Execute setup-ai.ps1.') from exc
    if not torch.cuda.is_available():
        raise ValueError('CUDA indisponível. Verifique driver NVIDIA e a instalação PyTorch cu128.')
    print(f'Carregando IA local em {torch.cuda.get_device_name(0)}...', flush=True)
    # Keep safety checker; safetensors only; no remote code or silent online model downloads.
    pipe = StableDiffusionPipeline.from_pretrained(str(MODEL_DIR), torch_dtype=torch.float16,
                variant='fp16', use_safetensors=True, local_files_only=True)
    pipe.scheduler = DEISMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.to('cuda')
    pipe.enable_vae_slicing()
    assets = path.parent / 'assets'
    assets.mkdir(exist_ok=True)
    report = {'model': MODEL_ID, 'revision': REVISION, 'generated': [], 'errors': []}
    try:
        for index, scene, prompt in pending:
            if len(studio.scene_assets(scene)) >= 8:
                report['errors'].append({'scene': index, 'error': 'Limite de oito materiais por cena.'})
                continue
            scene_seed = (seed + index - 1) % (2**32)
            print(f'Gerando imagem IA da cena {index}, seed {scene_seed}...', flush=True)
            try:
                if len(pipe.tokenizer(prompt).input_ids) > pipe.tokenizer.model_max_length:
                    raise ValueError('Prompt longo demais para o modelo. Encurte image_prompt; nada será truncado silenciosamente.')
                result = pipe(prompt, negative_prompt=NEGATIVE, num_inference_steps=steps,
                              guidance_scale=6.5, width=768, height=432,
                              generator=torch.Generator(device='cuda').manual_seed(scene_seed))
                if result.nsfw_content_detected and any(result.nsfw_content_detected):
                    raise ValueError('Imagem rejeitada pelo filtro do modelo; reformule a cena.')
                name = f'ai-{index:02}-{datetime.now().strftime("%Y%m%d-%H%M%S-%f")}.png'
                target = assets / name
                result.images[0].save(target)
                record = {'model': MODEL_ID, 'revision': REVISION, 'prompt': prompt, 'negative_prompt': NEGATIVE,
                          'seed': scene_seed, 'steps': steps, 'guidance_scale': 6.5, 'width': 768, 'height': 432,
                          'generated_at': datetime.now(timezone.utc).isoformat(), 'synthetic': True,
                          'sha256': studio.file_hash(target), 'file': target.relative_to(path.parent).as_posix()}
                studio.write(target.with_suffix('.generation.json'), record)
                shot = {'visual': record['file'], 'asset_origin': f'https://huggingface.co/{MODEL_ID}',
                        'asset_rights': 'Generated locally; model CreativeML Open RAIL-M terms apply',
                        'asset_title': 'AI-generated illustrative reconstruction', 'creator': 'Local diffusion model',
                        'synthetic': True, 'visual_context': 'AI reconstruction, not documentary evidence',
                        'generation_record': target.with_suffix('.generation.json').relative_to(path.parent).as_posix()}
                scene['visuals'] = [dict(s) for s in studio.scene_assets(scene)] + [shot]
                scene.pop('visual', None)
                data['ai_disclosure'] = 'yes'
                data.pop('review', None)
                studio.write(path, data)
                report['generated'].append(record)
            except Exception as exc:
                report['errors'].append({'scene': index, 'error': str(exc)})
                print(f'Falha cena {index}: {exc}', flush=True)
                if isinstance(exc, torch.cuda.OutOfMemoryError):
                    break
    finally:
        del pipe
        gc.collect()
        torch.cuda.empty_cache()
    studio.write(path.with_name(path.stem + '-ai.json'), report)
    if report['errors']:
        raise ValueError('Geração incompleta. Resultados concluídos foram preservados; consulte o relatório -ai.json.')
    print(f'{len(report["generated"])} imagens IA geradas localmente.')
    return report


if __name__ == '__main__':
    download_model()
