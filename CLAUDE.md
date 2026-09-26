# Atualização vigente — estilo jovem com trap (2026-09-25)

Esta configuração substitui as orientações antigas de vídeos fixos de 10 minutos, trilha ambiente, duas fotos por cena e entregas de descrição/SRT/thumbnail.

- Novo padrão: `production_style: youth-v1`, executado por `studio.py render` e `youth_renderer.py`. Não copie os antigos `projects/*/render_final.py`: são receitas arquivadas dos episódios anteriores.
- Inglês conversado, voz masculina Kokoro aprovada (75% Fenrir, 25% Michael). Contrações, exemplos fáceis, humor e gírias ocasionais que caibam na frase. Nada de bordões repetidos, suspense vazio ou texto esticado.
- Duração natural: 480–900 segundos, incluindo encerramento de 1,5 s. O programa rejeita roteiros fora do intervalo para revisão; não força dez minutos. Protótipos usam `--preview` e `preview_seconds` explícito.
- Ao menos 80% do TEMPO de tela deve ser vídeo real em movimento; preferir 90–100%. Planejar trechos relevantes de 3–6 s, variar cenas e não substituir explicação por corrida aleatória. Fotos só quando ajudam a explicar um detalhe.
- Trilhas originais locais: Midnight Pursuit, trap instrumental de ação, 152 BPM, 808 saturado, kick forte, caixa/clap, hi-hats rápidos e motivo sombrio. Mix padrão -10 dB após normalização, com redução automática sob a voz. Sem samples de terceiros.
- Sem referências no canto. Origem/licença permanecem apenas nos registros internos. Não confundir retirada de rótulos de fonte com permissão para apresentar imagens sintéticas como gameplay verdadeiro.
- Callouts opcionais; lista vazia por padrão. Usar `{text,start,duration}` para acertar o momento da fala. Pelo menos 10 s entre entradas e no máximo 18% do tempo com callouts. Preferir um destaque a cada 2–3 cenas.
- Entrega: somente MP4. Sem descrição, legendas (nem faixa embutida), thumbnail. Roteiro e proveniência são arquivos internos de produção.
- Footage: trailers oficiais curtos com comentário original, gravação própria ou gameplay de terceiros com licença/autorização verificável. Trailers Rockstar continuam protegidos. Não aceitar apenas o título “no copyright” como evidência. O buscador Commons mantém filtro de licença e agora tenta quatro vídeos por cena, com no máximo uma imagem. Resultados sem relevância/licença não viram preenchimento.
- Shots: `visual` (arquivo local), `start` (segundos de entrada), `seconds` (peso de duração), `crop` opcional `[largura,altura,x,y]`, `asset_origin`, `asset_rights`. O programa nunca repete automaticamente um clipe curto: exige trecho suficiente e verifica quadros decodificados.
- A voz usa o ambiente instalado em `work/voice-audition/.venv`; o render usa `.venv` do studio. GPU NVIDIA para vídeo. Sem serviços pagos nem upload automático.

Comandos:

```
run.cmd new projects/meu-video/project.json --channel gaming
run.cmd draft projects/meu-video/project.json --topic "Tema pesquisado"
run.cmd videos projects/meu-video/project.json --per-scene 4
run.cmd render projects/meu-video/project.json
run.cmd render projects/youth-trap-prototype/project.json --preview
```

Antes do render final, revisar o roteiro e planejar os trechos/fontes no projeto. A duração é calculada após a síntese. O protótipo de referência tem 30 s, oito trechos de trailers oficiais, 100% vídeo e dois callouts; não possui imagens estáticas nem legendas.

As seções antigas abaixo documentam versões anteriores e não substituem estes padrões.

---

# Development handoff

Communicate in Portuguese. English faceless videos, synthetic voice, maximum 600 seconds. Two profiles: GTA 6 / games and documented company histories. Free local tools preferred. Do not promise monetization.

Read README.md, POLITICAS-YOUTUBE.md, THIRD_PARTY.md and config/channels.json. studio.py implements CLI; run.cmd is the Windows entry point. Python 3.12, requirements.txt, local .venv and models directory.

Implemented: projects, automated research (Wikipedia, GDELT and RSS, bounded unverified excerpts), Commons photo search/download with PD/CC0 allowlist and optional CC BY, per-file license evidence, multiple shots per scene, pan/zoom, photo thumbnails and credits. Default voice is male en_US-joe-medium, length_scale 1.08. Source references, review fingerprints/asset hashes, timed SRT/MP4 subtitles, metadata and duration/decode verification remain. Sentence boundaries use measured audio; captions inside sentences use approximate timing. Ollama adapter consumes collected source notes and generates visual_query; live model integration remains untested, model not installed.

Version 0.3 adds local GPU image generation (ai_images.py, Absolute Reality 1.81, pinned revision, PyTorch 2.7.1 cu128) and license-filtered Commons footage (video_assets.py). Photo zoompan was removed to eliminate integer-crop jitter; photos now remain fixed. Read IA-E-VIDEOS.md. AI dependencies/model are installed and live generation succeeded on the RTX 5060. Generated images have provenance, synthetic=true, disclosure=yes and on-screen labels. Output is 768x432 upscaled for video. Do not represent it as archival evidence or GTA footage.

Version 0.4 supersedes fixed photos: presentation.py streams bicubic subpixel affine frames, smoothstep zoom 1.8%, capped at 2.5%, no integer zoompan. It overlays short callouts and synthesizes original ambient music locally with ducking. Read DINAMICA.md for controls. No third-party music samples. Dynamic demo is a technical preview, not editorial approval.

Not implemented: semantic image relevance verification, automatic fact checking, GUI, upload/scheduling. GDELT returned 429 in live tests; RSS fallback did collect gaming news. Review records support human editing, never certify policy compliance. Do not publish previews automatically.

Hardware: user reports 32 GB RAM; RTX 5060 with 8151 MiB VRAM verified. Current voice/encoding use CPU. Ask before multi-GB model downloads unless authorized.

Tests: .venv/Scripts/python.exe -m unittest discover -s tests -v
Smoke: run.cmd render examples/demo.json --preview --quality preview

Known limitations: clips loop with original sound muted; downloaded clips use first 12 seconds; automatic crops may miss the subject; matching is by query keywords; retries regenerate rather than resume. No source-footage stabilization. Final export requires visuals in every scene; only previews allow fallback cards. Preserve user content and previous renders. Run mutations sequentially for a given project JSON. Consult actual status.json files before claiming successful output.

Version 0.5: default photo_zoom=.08 (max .12), full-shot smoothstep movement; explicit older settings stay unchanged. Kinetic Impact typography, per-word staggered rise/settle, accent final word, outline/shadow, no callout boxes. Music synthesis/mix unchanged per user approval. examples/youth-demo is the current demo. Read DINAMICA.md.

GTA VI authored 10-minute episode: projects/gta6-before-launch. Official sources checked 2026-09-07. prepare.py is initial scaffolding and must not overwrite the populated project. build_episode.py uses cached sentence narration and frames allocated to 600s; render_tail.py produced final six segments in a separate folder; finalize.py adds fixed disclosure and verifies exactly 18,000 decoded frames. See episode README and FINAL-VERIFICATION.json. Delivery ../GTA6-10-minutes.mp4 plus thumbnail, description, SRT. No publishing/upload.

Critical mixed-media fix: presentation.encode_photo writes SAR=1. decorate_segment uses -reinit_filter 0 on the normalized main input; photo/stock color metadata changes otherwise reset setpts and drop the first shot. Regression test with bt470bg footage reproduces 62/120 frames without the fix and 120/120 with it. Current suite: 27 tests. repair_mixed.py repairs the first episode’s already-cached affected segments; normal new renders use the core fix.
