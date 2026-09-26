# Ferramentas e voz

Dependências em ambiente isolado. Estes links não substituem os textos das licenças.

- Piper: motor local GPL-3.0. https://github.com/OHF-Voice/piper1-gpl . Observar obrigações da licença se distribuir um aplicativo que o inclua. API: https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/API_PYTHON.md .
- Voz en_US-ljspeech-high: ficha indica dataset em domínio público e voz inglesa feminina. https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/ljspeech/high/MODEL_CARD . Dataset: https://keithito.com/LJ-Speech-Dataset/ . Repositório: https://huggingface.co/rhasspy/piper-voices . Conferir cada voz separadamente; não extrapolar os termos para outros modelos.
- FFmpeg via imageio-ffmpeg: https://github.com/imageio/imageio-ffmpeg e https://ffmpeg.org/legal.html . Observar termos do binário e sua configuração antes de redistribuí-lo.
- Pillow: https://github.com/python-pillow/Pillow/blob/main/LICENSE .
- Ollama opcional: https://docs.ollama.com/api/generate . Modelo proposto, não baixado: https://ollama.com/library/qwen3:4b .

A voz pode ser substituída após ouvir a demonstração. Materiais visuais de terceiros continuam sujeitos aos seus próprios direitos.

## Versão 0.2

- A voz padrão agora é **en_US-joe-medium**, masculina. Sua ficha identifica o dataset como CC0: https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/joe/medium/MODEL_CARD . A ficha também informa ajuste a partir de Lessac. Dataset: https://github.com/OHF-Voice/voice-datasets . O modelo Ryan não foi escolhido, pois sua ficha informa dataset CC BY-NC-SA.
- Fotografias: Wikimedia Commons, com licença por arquivo registrada em assets/*.license.json. Reutilização: https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia . CC0: https://creativecommons.org/publicdomain/zero/1.0/ . Domínio público/CC0 são os filtros padrão; CC BY exige --allow-attribution e preservação dos créditos.
- APIs: https://www.mediawiki.org/wiki/API:Imageinfo e https://www.mediawiki.org/wiki/API:Search .
- Pesquisa: GDELT https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/ , feeds de PC Gamer, GamesRadar e BBC Business; contexto da Wikipedia. Textos são fontes de pesquisa, não materiais visuais licenciados automaticamente.
- Extração de páginas: Trafilatura https://trafilatura.readthedocs.io/en/latest/usage-python.html .

## Versão 0.3

- IA local: Absolute Reality 1.81, Lykon, revisão 569d201654dca1426f1e090fca3953acc7db2c30, licença CreativeML Open RAIL-M. https://huggingface.co/Lykon/absolute-reality-1.81 . Modelo derivado de Stable Diffusion 1.5; termos e restrições da licença se aplicam. Não tratar outputs como automaticamente livres de quaisquer direitos. Proveniência e hashes em models/absolute-reality-1.81/provenance.json; prompts por imagem em assets/*.generation.json.
- Runtime: PyTorch 2.7.1 cu128, Diffusers 0.35.1, Transformers 4.55.4, Accelerate 1.10.1, Safetensors 0.6.2. https://pytorch.org/blog/pytorch-2-7/ e https://huggingface.co/docs/diffusers/en/using-diffusers/loading .
- Clipes: API videoinfo do Commons, com domínio público/CC0 por padrão e CC BY opcional. https://www.mediawiki.org/wiki/Extension:TimedMediaHandler/API . Não presume que um vídeo está liberado só por estar no YouTube ou na internet.
- Clipe da amostra: Pulping machines at the Museu Molí Paperer de Capellades, identificado como CC0 no Commons. Origem: https://commons.wikimedia.org/wiki/File:Pulping_machines_at_the_Museu_Mol%C3%AD_Paperer_de_Capellades.ogv . A amostra remove áudio e usa o vídeo para ilustrar produção de papel, sem atribuí-lo a uma empresa específica.
