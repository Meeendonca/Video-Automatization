# Verificação da implementação — 2026-09-05

- Oito testes unitários passaram: fonte exigida para fatos, referência inexistente, revisão alterada, material modificado, caminho fora da pasta, integridade das legendas/timestamps, resposta inválida do modelo sem sobrescrever projeto e rejeição de áudio acima do orçamento.
- Prévia gaming: 2 cenas, 1280×720, narração Piper, cartões originais, legendas SRT e faixa MP4. Duração verificada: 17,05 segundos. Decodificação completa passou; frame inicial inspecionado visualmente.
- Teste company_stories: entrada de clipe local, narração, exportação revisada técnica em 1920×1080. Decodificação completa passou. Teste em work/clip-smoke, sem publicação.
- Não foi feito teste com modelo Ollama real (não instalado), vídeo completo de dez minutos, avaliação auditiva humana ou upload ao YouTube.
- Requirements-lock.txt registra versões exatas instaladas. A voz roda por CPU; nenhum benchmark CUDA foi feito.

A demonstração prova o fluxo técnico, não qualidade editorial final ou elegibilidade de monetização.

## Versão 0.2 — pesquisa, fotos e voz masculina

- 17 testes passaram, incluindo filtro de licenças NC/ND/desconhecidas, opção explícita de atribuição, rejeição de endereços privados, deduplicação de pesquisa, falhas de provedores, múltiplos materiais na revisão e rejeição de exportação final sem fotos/clipes.
- Pesquisa real sobre GTA 6 coletou 6 fontes: 3 de contexto enciclopédico e 3 notícias de feeds. GDELT respondeu 429; o erro foi registrado. Não foi validada a veracidade das notícias automaticamente.
- Pesquisa real sobre Eastman Kodak coletou 3 fontes de contexto, sem notícias novas. O relatório informa zero notícias.
- Busca real no Wikimedia Commons baixou imagens com licença CC0/domínio público e evidências por arquivo. Uma consulta sem resultado permitido produziu aviso. A consulta de Rochester foi refinada para New York após inspeção, demonstrando a limitação de correspondência por palavras-chave.
- Nova prévia em 1920×1080: 2 cenas, 4 fotografias, movimento suave, voz masculina Joe, legendas, créditos e thumbnail fotográfica. Renderização e decodificação completas passaram. Frames foram inspecionados visualmente.
- Joe instalado e usado; dataset identificado como CC0 na ficha do modelo. Naturalidade/agradabilidade devem ser avaliadas pelo usuário ouvindo a amostra.
- Geração por IA de imagens não foi implementada: a alternativa escolhida foi fotografia real com licença explícita. Ollama e upload continuam sem integração real testada.

## Versão 0.3 — resultados posteriores

- 23 testes passaram. Casos novos cobrem seleção de vídeo relacionado, Ogg com MIME application/ogg, rejeição de licença não comercial, instruções quando falta o modelo, bloqueio de divulgação incorreta de IA e ausência de zoompan na fotografia.
- PyTorch CUDA e Absolute Reality 1.81 foram instalados. A geração local na RTX 5060 completou 28 passos em aproximadamente 3–4 segundos, além do carregamento. Modelo gera 768×432; não houve comparação sistemática de modelos nem teste de várias resoluções.
- Vídeo CC0 real de maquinaria de papel baixado, convertido e decodificado. A compatibilidade Ogg foi corrigida após o teste real.
- Nova amostra de 30,45 segundos em 1080p combina foto fixa, imagem IA identificada e clipe. Arquivo passou por validação de duração e decodificação completa. Frames foram inspecionados.
- Foto fixa: comparação de enquadramento em 0, 2, 4, 6 e 8 segundos estimou deslocamento [0,0] nos quatro pares, por correlação de fase em 480×270. Os hashes dos quadros diferem devido à compressão H.264; o teste não alega identidade de pixels nem estabilização do vídeo de origem.
- A geração por IA está implementada e testada nesta versão, substituindo a limitação anotada na 0.2. Ollama e upload continuam não testados com serviço real.


## Versão 0.4 — 2026-09-07

26 testes passaram. Prévia dinâmica real renderizada em 1080p/30 fps: 30,59 s, três cenas com foto, imagem IA e clipe. Decodificação integral FFmpeg com -xerror concluída sem erro. Quadros dos textos inspecionados: leitura clara, identificação de IA preservada. Zoom monotônico de 1 a 1,018, interpolação bicúbica fracionária e início/fim suaves verificados em teste.

Áudio final: média -23,6 dBFS, pico -2,7 dBFS; voz sem música: média -23,6 dBFS, pico -2,8 dBFS. Mistura sem clipping nos samples decodificados. Trilha original sintetizada, normalização -18 LUFS seguida de ganho -12 dB e ducking. Não foi feita avaliação auditiva humana; o usuário pode conferir conforto e preferência na prévia.

Render: examples/dynamic-demo/renders/20260907-153606-772142/preview.mp4. Cópia de entrega: ../youtube-dynamic-demo.mp4. A amostra permanece prévia técnica, sem aprovação editorial automática.


## Versão 0.5 — edição jovem

26 testes passaram. Prévia 1080p/30 fps concluída com decodificação integral sem erros: 30.12 s. Entrada progressiva das palavras e leitura da tipografia inspecionadas em quadros a 0,47/0,57/0,8/5,7 s. Aproximação padrão aumentada para 8% por plano, máximo 12%; sem alterar a trilha e os parâmetros de mixagem aprovados. Entrega: ../youtube-youth-demo.mp4. Configurações: examples/youth-demo/project.json.


## GTA VI: episódio completo — 2026-09-07

Entrega: ../GTA6-10-minutes.mp4. 600 segundos, 18.000 quadros decodificados, H.264 1920x1080, 30 fps. Decodificação integral passou; áudio médio -23,5 dBFS e pico -2,8 dBFS. 27 testes passaram, incluindo regressão real de mistura foto/clipe com metadados de cor diferentes. A reinicialização do grafo de filtros perdia a primeira imagem; corrigida e três cenas recuperadas com contagens 723/723, 836/836 e 640/640. Exportação final normaliza PTS para começar em zero. Evidência: projects/gta6-before-launch/FINAL-VERIFICATION.json.
