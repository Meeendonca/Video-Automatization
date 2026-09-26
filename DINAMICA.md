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

# Textos, movimento leve e música

O estilo novo é aplicado ao renderizar. Projetos sem photo_zoom usam 8%; valores explícitos antigos, como 0.018, são preservados: altere-os para 0.08 se quiser a aproximação maior. A demonstração está em `examples/youth-demo/project.json`.

Na raiz do JSON, configure a trilha:

```json
"music": {"enabled": true, "gain_db": -12}
```

A trilha Quiet Workshop é uma composição instrumental sintetizada pelo próprio programa, sem downloads, gravações ou samples de terceiros. Usa acordes suaves e notas espaçadas, sem bateria. É gratuita e funciona offline. O áudio é normalizado para -18 LUFS antes da redução de 12 dB; o volume cai ainda mais durante a narração. O limitador protege a mistura contra picos. `gain_db` aceita -24 (mais baixo) até -8 (mais alto); `enabled: false` desliga a trilha. Não é possível garantir ausência de falsos positivos de Content ID.

Em cada cena, acrescente:

```json
"photo_zoom": 0.08,
"callouts": ["EVERY OBJECT HAS A STORY", "HOW WAS IT MADE?"]
```

A aproximação padrão é de **8% no total por imagem**, distribuídos por toda a duração do plano, com início e fim suaves e coordenadas fracionárias. Não há balanço lateral. O limite é 12%; `0` desliga. Clipes mantêm o movimento da filmagem original.

Cada chamada aparece por até 2,3 segundos. A tipografia grande e condensada tem contorno escuro para leitura sobre a imagem, palavra final em cor viva e entrada palavra por palavra a cada 85 ms. As palavras sobem 42 pixels e assentam com um pequeno retorno de 4 pixels; o texto permanece estável depois da entrada. Não são usadas caixas de apresentação. Use frases curtas em inglês, idealmente 2–6 palavras. São aceitos até cinco textos por cena, de até 64 caracteres cada. Sem `callouts`, aparece o título da cena; `[]` desliga. Cenas curtas podem omitir chamadas que não teriam tempo de leitura. As legendas da narração continuam disponíveis separadamente.

```powershell
.\run.cmd render examples/youth-demo/project.json --preview
```

O render salva MP4, trilha original WAV, créditos e configurações na pasta `renders` do projeto. A prévia é técnica e não recebe aprovação editorial automática. Alterar as configurações do JSON invalida uma aprovação existente. A renderização com aproximação usa CPU e demora mais que a imagem estática.
