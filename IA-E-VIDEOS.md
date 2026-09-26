# Versão 0.3 — imagens estáveis, IA local e clipes

Nesta máquina, PyTorch CUDA, Diffusers e Absolute Reality 1.81 já estão instalados. A geração foi executada na RTX 5060. Não usa API paga. O modelo ocupa aproximadamente 2 GB, além das dependências; a instalação completa precisa de vários GB. As imagens são geradas em 768×432 e dimensionadas para o vídeo em 1080p; não são imagens nativas de 1080p.

## Correção da tremedeira

Foi removido o zoompan das fotografias. O enquadramento é calculado uma vez, com reamostragem Lanczos; as fotos ficam fixas. Vídeos mantêm seu movimento original. Isso corrige o movimento artificial da montagem anterior, mas não estabiliza automaticamente uma filmagem de câmera na mão. Renderizações antigas são preservadas; execute render novamente para aplicar a correção.

## Imagens por IA

Em cada cena, defina image_prompt em inglês, de preferência com uma ou duas frases curtas sobre um objeto, ambiente e iluminação. Exemplo:

```json
"image_prompt": "An unbranded vintage film camera on a dark wooden workbench, soft warm window light, detailed glass lens"
```

```powershell
.\run.cmd generate-images projects/episode/project.json --scene 2
```

Sem --scene, processa todas as cenas elegíveis. Por padrão, só preenche cenas vazias. Para adicionar uma imagem a uma cena que já contém fotos ou clipes:

```powershell
.\run.cmd generate-images projects/episode/project.json --scene 2 --append --seed 42 --steps 28
```

Cenas que já têm uma imagem marcada synthetic são ignoradas; para gerar outra versão, faça uma cópia do projeto e remova a entrada sintética da lista visuals. Os arquivos anteriores são preservados. O prompt pode usar visual_query como alternativa, mas image_prompt oferece mais controle. Prompts acima da capacidade do modelo são rejeitados em vez de truncados silenciosamente.

Cada imagem tem um arquivo .generation.json com prompt, prompt negativo, seed, parâmetros, revisão do modelo e hash. Imagens realistas geradas recebem synthetic=true, ai_disclosure=yes e identificação discreta no vídeo. Elas são reconstruções ilustrativas, não provas de fatos nem capturas de GTA. O modelo mantém seu filtro de conteúdo. A imagem pode apresentar erros de objetos/perspectiva; revise-a.

O modelo é Absolute Reality 1.81 (Lykon), com licença CreativeML Open RAIL-M. Os termos do modelo se aplicam; imagens geradas não recebem uma declaração automática de domínio público. Não há custo de API, mas existe consumo local de energia e armazenamento.

## Vídeos relacionados

Defina video_query com o objeto ou ação concreta. O comando usa visual_query se video_query não existir.

```json
"video_query": "pulping machines"
```

```powershell
.\run.cmd videos projects/episode/project.json --scene 3
```

A busca usa Wikimedia Commons. Por padrão, aceita vídeos identificados como domínio público ou CC0. A correspondência verifica palavras da consulta no título/descrição, não apenas no resultado de busca. Não é seleção semântica: assista ao clipe e confira a relevância. Consultas vagas podem não encontrar nada; não substituímos o tema por outro sem avisar.

Os clipes entram em visuals junto dos materiais existentes. O comando preserva cenas que já tenham um clipe automático. Limite de oito materiais por cena. Opcionalmente, --allow-attribution admite CC BY e inclui créditos. Não admite NC/ND/BY-SA automaticamente.

Baixa até 120 MB por candidato, extrai até os primeiros 12 segundos, remove o áudio original e converte para MP4 720p/30fps. Isso evita reutilizar a trilha sonora incidental. O arquivo final é decodificado para verificação. Se o trecho inicial for inadequado, use outro clipe ou edite o material localmente. Na montagem, trechos curtos podem se repetir para preencher a cena.

Origem, autor, licença e alterações ficam em .license.json, credits.txt e metadata.json. Licença explícita não equivale a garantia universal de ausência de direitos de imagem/marca. Não remova créditos exigidos. Falhas ficam em project-videos.json e os materiais anteriores são preservados.

## Demonstração e renderização

```powershell
.\run.cmd render examples/ai-video-demo/project.json --preview
```

A demonstração tem uma fotografia fixa, uma imagem IA de câmera e um vídeo CC0 de maquinaria de papel, com narração masculina. É uma amostra das capacidades, não um episódio final sobre uma empresa.

Para seu episódio: research → draft (Ollama opcional) → visuals / generate-images / videos → render --preview → revisão → review → render. Execute os comandos em sequência para o mesmo arquivo de projeto. Não há publicação automática.

## Instalar a IA em outro computador

Primeiro execute setup.ps1. Depois:

```powershell
.\setup-ai.ps1
```

Alternativa manual se scripts PowerShell estiverem bloqueados:

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
.\.venv\Scripts\python.exe -m pip install -r requirements-ai.txt
.\.venv\Scripts\python.exe -X utf8 ai_images.py
```

O download usa uma revisão fixa do modelo, safetensors e arquivos locais; a inferência posterior funciona offline. Ao faltar VRAM, feche outros programas que usam GPU e tente novamente. Não há fallback silencioso para um serviço pago.

Fontes técnicas: [modelo](https://huggingface.co/Lykon/absolute-reality-1.81), [Diffusers](https://huggingface.co/docs/diffusers/en/using-diffusers/loading), [PyTorch CUDA](https://pytorch.org/blog/pytorch-2-7/), [API de vídeos Commons](https://www.mediawiki.org/wiki/Extension:TimedMediaHandler/API).
