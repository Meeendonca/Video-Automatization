# YouTube Video Studio

Programa local para pesquisa, roteiros em inglês, voz artificial e edição de vídeos com foco em GTA e games.

## Estado desta versão

Código completo do programa, com o estilo de edição e música aprovados. Interface por comandos, sem interface gráfica. Não publica automaticamente no YouTube.

Esta cópia inclui código, configuração, documentação e testes. Vídeos, trailers, modelos de voz/IA, ambientes Python e episódios produzidos não são incluídos.

**Instalação ainda depende da configuração local:** o renderizador jovem usa o ambiente Kokoro e modelos em `work/voice-audition` da estrutura original do projeto. O script `setup.ps1` instala o ambiente legado Piper, não prepara sozinho o novo Kokoro. Ajuste esses caminhos em `youth_renderer.py` ao instalar em outro computador. O exportador jovem requer NVIDIA/NVENC. Não é uma distribuição pronta para instalar com um clique.

Leia `ESTILO-JOVEM.md` para as regras atuais e `THIRD_PARTY.md` para as dependências e materiais externos. As demais seções abaixo incluem histórico de versões.

---

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

# YouTube Studio local

Programa de linha de comando para dois canais: GTA 6 / lançamentos e histórias documentadas de empresas. Conteúdo em inglês, voz artificial, sem apresentador, até 600 segundos. Não usa APIs pagas.

**Versão 0.5:** tipografia jovem com entrada palavra por palavra, aproximação suave de 8% ao longo do plano e música ambiente original sintetizada localmente, com redução durante a fala. Veja [ajustes visuais e música](DINAMICA.md). Inclui pesquisa automática, IA local na RTX, clipes com licença registrada e voz masculina Joe: [IA e vídeos](IA-E-VIDEOS.md), [pesquisa](USO-AUTOMATICO.md).

## Implementado

Criação de projetos, pesquisa em Wikipedia/GDELT/feeds, registro de fontes, revisão vinculada ao roteiro e materiais, voz masculina local Piper, montagem de fotografias/clipes, MP4 1080p/30 fps, legendas SRT e faixa selecionável no MP4, thumbnail com fotografia, créditos e validação da duração/decodificação. Integração opcional com Ollama para rascunhos a partir das fontes coletadas.

A validação estrutural não verifica fatos, direitos autorais ou elegibilidade para monetização. Nenhum vídeo é enviado ao YouTube.

## Usar neste computador

Abra o terminal nesta pasta. O ambiente .venv, FFmpeg e a voz já estão instalados.

```powershell
.\run.cmd doctor
.\run.cmd render examples/demo.json --preview --quality preview
.\run.cmd render examples/visual-demo/project.json --preview
```

A demonstração é técnica, não uma notícia de GTA. Cada tentativa cria uma pasta renders junto ao JSON e imprime o caminho do MP4. Não substitui tentativas anteriores.

## Produzir um episódio

```powershell
.\run.cmd new projects/gta-episode/project.json --channel gaming
# Para o outro canal: --channel company_stories
```

Edite o JSON em um editor:

| Campo | Conteúdo |
|---|---|
| title / description | Título e descrição em inglês |
| sources | Lista com id, url, accessed_at e notes contendo fatos conferidos e data de publicação |
| scenes[].heading | Título curto da cena |
| scenes[].narration | Texto exato em inglês |
| scenes[].claim_type | fact, rumor, analysis ou fiction |
| scenes[].source_ids | IDs das fontes; obrigatório para fact e rumor |
| scenes[].visual | PNG/JPEG/WebP/MP4/MOV/MKV, caminho relativo dentro da pasta do episódio; null gera cartão |
| scenes[].visual_query | Objeto/lugar concreto em inglês para busca automática de fotos |
| scenes[].visuals | Lista de materiais; preenchida pelo comando visuals; permite várias fotos por cena |
| scenes[].asset_origin | URL ou registro da origem |
| scenes[].asset_rights | Licença, permissão ou fundamento de uso verificado |
| ai_disclosure | yes, no ou undecided; decidir antes da exportação revisada |

Copie os materiais para a pasta do episódio, por exemplo assets/shot1.png. Registre fontes reais, preferencialmente primárias. Rumores devem ser identificados também na fala. Em controvérsias, distinguir acusações de conclusões e considerar respostas das empresas.

```powershell
.\run.cmd validate projects/gta-episode/project.json
.\run.cmd render projects/gta-episode/project.json --preview --quality preview
```

Revise fatos, originalidade, materiais, pronúncia, legendas e a decisão sobre IA. Depois registre sua revisão:

```powershell
.\run.cmd review projects/gta-episode/project.json --reviewer "Fernando"
.\run.cmd render projects/gta-episode/project.json
```

review registra sua declaração, não faz análise automática. Alterações no projeto ou nos materiais invalidam a aprovação. Arquivos finais: video.mp4, captions.srt, thumbnail.png, metadata.json, project.json e status.json. Prévia gera preview.mp4. Ative legendas no player ou envie o SRT no YouTube Studio; elas não estão queimadas na imagem.

## Roteiro com IA local (opcional)

Instale [Ollama](https://ollama.com/download/windows) e execute:

```powershell
ollama pull qwen3:4b
```

Esse download tem vários GB e não foi executado nesta entrega. Consulte tamanho/licença na [página do modelo](https://ollama.com/library/qwen3:4b). É um ponto inicial para experimentar com 8 GB de VRAM; ainda não houve benchmark local. O serviço deve responder em 127.0.0.1:11434.

Colete fontes com research, revise o relatório e execute:

```powershell
.\run.cmd draft projects/gta-episode/project.json --topic "Your specific evidence-backed angle" --minutes 8
```

Salva project-draft.json sem substituir o original. O modelo recebe tema, perfil e notas coletadas por research; não navega por conta própria. Revise o rascunho e execute visuals no arquivo de rascunho. O alvo de palavras é estimado; o limite real é verificado após sintetizar e renderizar.

## Instalar em outra máquina

Use Python 3.12 de [python.org](https://www.python.org/downloads/windows/).

```powershell
.\setup.ps1 -Python python
```

Se a política local bloquear scripts PowerShell, execute manualmente:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m piper.download_voices --download-dir models en_US-joe-medium
.\run.cmd doctor
```

A instalação precisa de internet; a renderização é local. FFmpeg vem com imageio-ffmpeg, sem alteração do PATH.

## Limites e próximos componentes

Ainda não há interface gráfica, música ou publicação/agendamento. Há fotografias da internet, geração IA local e busca de clipes no Commons. Os dois canais usam Joe por padrão; substitua com --voice caminho/modelo.onnx, acompanhado de modelo.onnx.json.

Voz e codificação usam CPU; a IA de imagens usa GPU. Clipes curtos são repetidos e seu áudio original é removido. Fotografias ficam fixas para evitar tremedeira; há cortes entre materiais. Cartões só são alternativa em prévias; exportação final exige imagens/clipes em todas as cenas. A voz sintetiza frases inteiras quando possível. Limites das frases usam duração real; alinhamento das legendas dentro de frases é aproximado. Revise a naturalidade e o enquadramento.

Para completar a automação:

1. Pesquisa: ampliar fornecedores além dos feeds/GDELT/Wikipedia implementados, e acrescentar verificação cruzada. Não usar memória do modelo como fonte de notícias.
2. Visuais: ampliar acervos além do Commons e adicionar seleção semântica. A geração local já funciona com Absolute Reality 1.81; evolução futura pode testar modelos maiores e resolução nativa superior.
3. Edição: adicionar cortes, gráficos e cenas específicas para cada argumento; depois trilha licenciada e mixagem. Evitar produção repetitiva em massa.
4. Publicação: implementar OAuth e YouTube Data API, começar com upload privado, enviar thumbnail/legendas e publicar após revisão. Tokens fora do Git. [Guia oficial](https://developers.google.com/youtube/v3/guides/uploading_a_video). Não implementado nem autenticado.

## Testes e falhas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Falhas preservam intermediários e status.json. Repetir o comando cria nova tentativa e refaz etapas; não há retomada automática. A narração tem orçamento de 599 segundos para acomodar frames; nunca cortamos a última frase. O MP4 final precisa ter no máximo 600 segundos e passar pela decodificação.

Leia POLITICAS-YOUTUBE.md e THIRD_PARTY.md. Para continuar no Claude Code, abra esta pasta e leia CLAUDE.md.
