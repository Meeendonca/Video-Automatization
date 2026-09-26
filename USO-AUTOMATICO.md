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

# Pesquisa, fotografias e voz masculina

Atualização 0.3: geração IA e busca de vídeos estão em [IA-E-VIDEOS.md](IA-E-VIDEOS.md). O zoom das fotos foi removido para eliminar a tremedeira.

Abra o terminal na pasta youtube-studio. Nesta máquina as dependências e a voz já estão instaladas. Em outra máquina, execute setup.ps1.

## Demonstração nova

```powershell
.\run.cmd render examples/visual-demo/project.json --preview
```

Usa fotografias reais, duas por cena, agora fixas, com voz masculina Joe em ritmo um pouco mais pausado. É uma demonstração técnica, não uma investigação pronta. Os enquadramentos automáticos precisam de avaliação humana. A voz é proposta para você ouvir e avaliar; a qualidade continua sendo a de um modelo local gratuito.

## Episódio com pesquisa automática

```powershell
.\run.cmd new projects/episode/project.json --channel gaming
.\run.cmd research projects/episode/project.json --query "GTA 6" --limit 8
```

Para empresas, use --channel company_stories e um tema como "Eastman Kodak". A pesquisa:

- Busca contexto na Wikipedia, notícias no GDELT e nos feeds configurados.
- Lê páginas públicas com Trafilatura, remove navegação quando possível e guarda trechos curtos com origem.
- Deduplica URLs e registra a data de publicação quando fornecida; datas desconhecidas ficam vazias.
- Marca tudo como não verificado. Não confunde contexto enciclopédico com notícia recente.
- Salva project-research.json com resultados e falhas. Não contorna bloqueios de sites.

GDELT pode responder 429. O programa registra isso e continua com os feeds e o contexto disponível. Se não houver notícias, diz zero notícias. A cobertura depende dos fornecedores; não é uma busca exaustiva de toda a internet.

Você pode incluir fontes primárias específicas:

```powershell
.\run.cmd research projects/episode/project.json --query "Your topic" --url "https://your-actual-primary-source/article"
```

O URL acima é ilustrativo. Para somente contexto histórico, use --background-only. As notas automáticas são trechos, não resumos factualmente certificados. Revise para remover fontes irrelevantes e acrescentar contexto antes de publicar.

## Roteiro e imagens

Com Ollama e qwen3:4b instalados, conforme README:

```powershell
.\run.cmd draft projects/episode/project.json --topic "Your original evidence-backed angle" --minutes 8
.\run.cmd visuals projects/episode/project-draft.json --per-scene 2
.\run.cmd render projects/episode/project-draft.json --preview --quality preview
```

Ollama continua opcional e não foi instalado nesta entrega. Também é possível escrever scenes manualmente e executar visuals/render diretamente. Cada cena deve ter visual_query, por exemplo "Miami skyline", "Kodak camera" ou "Rochester New York skyline". Inclua estado/país quando houver locais com o mesmo nome. Use objetos e locais concretos; títulos abstratos como "The hidden truth" produzem buscas ruins.

visuals busca no Wikimedia Commons e aceita, por padrão, somente arquivos identificados como domínio público ou CC0 nos metadados. Guarda página original, autor, licença, metadados e hash em assets/*.license.json. Se precisar ampliar o acervo:

```powershell
.\run.cmd visuals projects/episode/project-draft.json --allow-attribution
```

Essa opção aceita também CC BY e gera os créditos. Não aceita NC, ND ou BY-SA automaticamente. Autor, licença e origem vão para credits.txt e para a descrição em metadata.json. Não remova os créditos necessários na publicação. Os metadados não garantem autoria correta ou ausência de direitos de imagem/marca; a página do arquivo deve ser revisada.

Nenhuma foto é inventada quando a busca falha. Mude visual_query ou forneça material próprio. Materiais já associados às cenas são preservados; para substituí-los, remova visuals da cena após salvar uma cópia do projeto. A correspondência é por palavras-chave, não por compreensão visual. Itens explicitamente identificados como IA/ilustração nos metadados são filtrados, mas isso não é um detector de imagens sintéticas. Fotos de Miami são ilustrações de Miami, nunca gameplay de GTA nem prova do que o jogo contém.

## Voz e finalização

Joe é a voz masculina padrão. voice_length_scale=1.08 dá um ritmo um pouco mais lento; 1.0 usa o ritmo padrão. Valores permitidos: 0.8 a 1.4. Não alteramos artificialmente a altura da voz.

Após ouvir e assistir à prévia, revisar fontes e decidir ai_disclosure:

```powershell
.\run.cmd review projects/episode/project-draft.json --reviewer "Fernando"
.\run.cmd render projects/episode/project-draft.json
```

O resultado inclui MP4, legendas, thumbnail, créditos e metadados. Não há publicação automática. Este guia cobre a pesquisa e as fotos da internet. A versão 0.3 também oferece geração local por IA e clipes; consulte IA-E-VIDEOS.md.
