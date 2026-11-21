# Serein

Aplicação de meditação responsiva com Flask, SQLite, cinco idiomas, narração por voz do dispositivo, upload de áudio, vídeo e música licenciada. Inclui Lumi, um mascote SVG, e guias visuais animados para acompanhar a respiração.

## Iniciar

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export SEREIN_ADMIN_PASSWORD='uma-senha-forte'
export SEREIN_SECRET_KEY='uma-chave-aleatoria-longa'
python app.py
```

Aceda a `http://127.0.0.1:5000`. A base SQLite e os dados iniciais são criados automaticamente. Defina `SEREIN_DB` e `SEREIN_UPLOADS` para outros caminhos. O botão de engrenagem abre a administração.

## API

- `GET /api/sessions?lang=pt|en|fr|it|es` — sessões publicadas.
- `GET /api/music` — gravações publicadas com metadados de licença.
- `POST /api/admin/login` — sessão administrativa. Envie o token devolvido em `X-CSRF-Token` nas alterações seguintes.
- `GET /api/admin/sessions`, `POST /api/admin/sessions`, `PATCH /api/admin/sessions/<id>` — gerir meditações.
- `POST /api/admin/upload` — upload de narração por sessão e idioma.
- `POST /api/admin/video` — upload de vídeo MP4, WebM ou MOV por sessão.
- `GET /api/admin/music`, `POST /api/admin/music`, `PATCH /api/admin/music/<id>` — gerir música com proveniência.

Novas meditações exigem os cinco textos e começam como rascunho. Novas faixas também começam como rascunho. Os textos iniciais são reflexões originais; não há citações atribuídas a filósofos nem gravações musicais sem licença. Sem áudio carregado, o player usa a síntese de voz local do navegador. O seed inclui três vídeos WebM originais de 12 segundos, reproduzidos em loop durante a sessão e sem áudio; a narração continua no idioma selecionado. Um vídeo enviado no admin substitui o vídeo do seed para aquela sessão. Para produção, use HTTPS, um proxy com limites de upload e uma chave de sessão persistente.

## Vídeos do seed

Os ficheiros ficam em `static/videos/`. Para recriá-los, execute `python3 scripts/generate_seed_videos.py` num ambiente com Pillow e FFmpeg. Cada vídeo é um loop visual original e silencioso de respiração, relaxamento ou sono.

## Práticas com referências de saúde

O seed adiciona três sessões estruturadas: respiração suave (5 min), relaxamento muscular progressivo abreviado (6 min) e atenção plena (5 min), em cinco idiomas. As etapas, tempos, orientações de conforto e fontes ficam em `exercise_protocols` no SQLite; `exercise_seed.json` contém os dados iniciais. O seed é idempotente e preserva alterações administrativas. Para reconstruir o JSON editorial, execute `python3 scripts/build_exercise_seed.py`.

As referências são NHS (respiração), VA Whole Health (relaxamento progressivo) e NCCIH/NIH (mindfulness). São adaptações originais de bem-estar, sem validação clínica desta aplicação; a adaptação breve de relaxamento não reproduz o protocolo completo e a introdução de mindfulness não equivale aos programas avaliados nos estudos. Referências e limites aparecem em cada exercício. Não há promessa de tratar ansiedade, insônia ou outras condições.

O player narra as instruções ao entrar em cada etapa e permite pausar, reiniciar e avançar. O contador de conclusões fica apenas no dispositivo. Novos protocolos não reutilizam vídeos com ritmos incompatíveis: o guia respiratório opcional usa ciclos de 10 segundos e as outras práticas deixam a respiração natural. A preferência por movimento reduzido é respeitada.

## Histórias, fundos sonoros e Android

Inclui duas histórias originais de quatro minutos, em português, inglês, francês, italiano e espanhol: **A enseada tranquila** e **O jardim depois da chuva**. Cada história tem seis capítulos cronometrados e fundo sonoro selecionável. O seed fica em `story_seed.json`; `scripts/build_story_seed.py` reconstrói os textos iniciais.

Os sons de mar e chuva são sintetizados originalmente para o projeto. O tema de Beethoven é um arranjo original sintetizado de **Ode to Joy**, composição em domínio público, com referência à partitura Mutopia #528. Os três fonogramas são dedicados a CC0; créditos e fontes ficam em `static/audio/credits.json`. `scripts/generate_soundscapes.py` os recria. A interface permite ajustar o volume e reduz o fundo durante a fala.

O [projeto Android](android/README.md) encapsula o mesmo HTML com assets e catálogo locais; não há URL pública ou permissão de internet. O APK de desenvolvimento fica em `dist/serein-debug.apk`. O splash possui o mascote Lumi. Os menus mobile dão acesso a início, práticas, histórias, sons e ritual.

A narração Android requer vozes offline instaladas para o idioma selecionado. As vibrações opcionais servem de marcadores táteis e não são estimulação médica do nervo vago. Histórias de visualização guiada são práticas de bem-estar, não uma validação clínica de sofrologia.

## Catálogo ampliado — novembro de 2026

O catálogo tem 16 sessões em cinco idiomas, com 11 práticas estruturadas. Foram adicionadas oito meditações autorais: começo do dia (3 min), pausa entre tarefas (3 min), escuta atenta (5 min), varredura corporal (8 min), gentileza consigo (6 min), acolhimento das emoções (5 min), desaceleração noturna (8 min) e caminhada consciente (5 min). Elas aparecem no site, na API e no catálogo offline Android.

Use busca, categoria e duração para escolher uma prática. O seed continua idempotente e preserva edições administrativas. Os roteiros adicionais estão em `scripts/expanded_meditations.py` e são incluídos ao executar `python3 scripts/build_exercise_seed.py`.

Validação: `python3 -m unittest discover -s tests -v`. APK atualizado: `dist/serein-variety-debug.apk`; veja as notas de assinatura em `android/README.md`.

## Voz calma e biblioteca sonora — versão 1.2.0

O player permite escolher a voz local por idioma, ouvir uma frase de teste, selecionar os ritmos Bem calmo, Calmo ou Natural, e ajustar velocidade, tom, pausa entre frases e volume da narração. O padrão Bem calmo usa velocidade 0,74 e pausa de 1,4 segundo entre frases. A qualidade do timbre depende da voz instalada. A sequência de fala é cancelada ao pausar, avançar de etapa, sair de primeiro plano ou fechar o player. As preferências de voz e som ficam no aparelho.

São dez fundos originais em estéreo: mar, chuva, floresta, riacho, lareira, noite, ruído marrom, piano, atmosfera musical e arranjo de Beethoven. Os sons de natureza são sintetizados, sem gravações de campo. Há filtro por tipo, amostra antes de escolher, botão Usar na sessão, volume separado e redução opcional do fundo durante a voz. Os arquivos têm 32 segundos, níveis equilibrados e junção suavizada para repetição. Créditos e métricas ficam em `static/audio/`. O gerador requer NumPy apenas para recriar os assets; o servidor Flask não depende de NumPy.

Teste do sequenciador: `node --test tests/test_audio_core.cjs`. Testes de catálogo e arquivos: `python3 -m unittest discover -s tests -v`.

APK de desenvolvimento atualizado: `dist/serein-calm-audio-debug.apk`. Mantém a chave debug persistida da versão 1.1.0 (catálogo ampliado), permitindo atualização sobre aquela compilação. Não há garantia de compatibilidade com o primeiro APK, que usou outra chave temporária.
