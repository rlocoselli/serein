# Serein

Aplicação de meditação responsiva com Flask, SQLite, cinco idiomas, narração natural em áudio, voz do dispositivo opcional, upload de áudio, vídeo e música licenciada. Inclui Lumi, um mascote SVG, e guias visuais animados para acompanhar a respiração.

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

## Docker

Construa a partir da raiz de qualquer branch: `main` tem um Dockerfile que usa as fontes em `web-meditation/`; a branch `web-meditation` usa as fontes na própria raiz. Também pode construir diretamente dentro de `web-meditation/` na branch `main`.

```bash
docker build --pull -t serein .
read -rsp 'Senha de administração: ' SEREIN_ADMIN_PASSWORD; echo
export SEREIN_ADMIN_PASSWORD
export SEREIN_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
docker run -d --name serein --restart unless-stopped \
  -p 127.0.0.1:5000:5000 \
  --mount source=serein-data,target=/data \
  -e SEREIN_ADMIN_PASSWORD -e SEREIN_SECRET_KEY \
  serein
```

Abra `http://127.0.0.1:5000`. Se a porta local já estiver ocupada, use `-p 127.0.0.1:5001:5000`. O volume `serein-data` guarda a base SQLite e os uploads; o catálogo inicial é criado automaticamente no primeiro arranque. A imagem inclui os vídeos e sons do seed, usa Gunicorn na porta interna 5000 e executa como utilizador sem privilégios. Chaves, bases locais, uploads existentes e builds Android ficam fora do contexto de construção.

Guarde os valores das duas variáveis num gestor de segredos ou ficheiro `.env` local protegido e reutilize-os ao recriar o contentor. Também pode fornecê-los com `--env-file .env`. Não inclua esse ficheiro na imagem ou no Git. Consulte o estado com `docker inspect --format '{{.State.Health.Status}}' serein` e os registos com `docker logs -f serein`.

Para plataformas de hospedagem, selecione a branch `main`, contexto de construção `.` e Dockerfile `Dockerfile`, sem comando de arranque adicional. O servidor e o healthcheck respeitam a variável `PORT` fornecida pela plataforma (padrão: `5000`). Configure `SEREIN_ADMIN_PASSWORD` e `SEREIN_SECRET_KEY` como segredos e monte armazenamento persistente em `/data` para conservar os conteúdos após um novo deploy.

## API

- `GET /api/sessions?lang=pt|en|fr|it|es` — sessões publicadas.
- `GET /api/music` — gravações publicadas com metadados de licença.
- `POST /api/admin/login` — sessão administrativa. Envie o token devolvido em `X-CSRF-Token` nas alterações seguintes.
- `GET /api/admin/sessions`, `POST /api/admin/sessions`, `PATCH /api/admin/sessions/<id>` — gerir meditações.
- `POST /api/admin/upload` — upload de narração por sessão e idioma.
- `GET /api/admin/narration/options`, `POST /api/admin/narration` — vozes disponíveis e geração de rascunho em segundo plano.
- `GET /api/admin/narration/<id>`, `POST /api/admin/narration/<id>/publish` — acompanhar, escutar e ativar um rascunho.
- `POST /api/admin/video` — upload de vídeo MP4, WebM ou MOV por sessão.
- `GET /api/admin/music`, `POST /api/admin/music`, `PATCH /api/admin/music/<id>` — gerir música com proveniência.

Novas meditações exigem os cinco textos e começam como rascunho. Novas faixas também começam como rascunho. Os textos iniciais são reflexões originais; não há citações atribuídas a filósofos nem gravações musicais sem licença. Sem áudio gravado, o player mantém o texto e o fundo sonoro; a síntese de voz do aparelho é uma opção explícita. O seed inclui três vídeos WebM originais de 12 segundos, reproduzidos em loop durante a sessão e sem áudio; a narração continua no idioma selecionado. Um vídeo enviado no admin substitui o vídeo do seed para aquela sessão. Para produção, use HTTPS, um proxy com limites de upload e uma chave de sessão persistente.

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

Na opção facultativa Voz do aparelho, o player permite escolher a voz local por idioma, ouvir uma frase de teste, selecionar os ritmos Bem calmo, Calmo ou Natural, e ajustar velocidade, tom, pausa entre frases e volume da narração. O padrão Bem calmo usa velocidade 0,74 e pausa de 1,4 segundo entre frases. A qualidade do timbre depende da voz instalada. A sequência de fala é cancelada ao pausar, avançar de etapa, sair de primeiro plano ou fechar o player. As preferências de voz e som ficam no aparelho.

São dez fundos originais em estéreo: mar, chuva, floresta, riacho, lareira, noite, ruído marrom, piano, atmosfera musical e arranjo de Beethoven. Os sons de natureza são sintetizados, sem gravações de campo. Há filtro por tipo, amostra antes de escolher, botão Usar na sessão, volume separado e redução opcional do fundo durante a voz. Os arquivos têm 32 segundos, níveis equilibrados e junção suavizada para repetição. Créditos e métricas ficam em `static/audio/`. O gerador requer NumPy apenas para recriar os assets; o servidor Flask não depende de NumPy.

Teste do sequenciador: `node --test tests/test_audio_core.cjs`. Testes de catálogo e arquivos: `python3 -m unittest discover -s tests -v`.

APK de desenvolvimento atualizado: `dist/serein-calm-audio-debug.apk`. Mantém a chave debug persistida da versão 1.1.0 (catálogo ampliado), permitindo atualização sobre aquela compilação. Não há garantia de compatibilidade com o primeiro APK, que usou outra chave temporária.

## Narração natural gratuita com Kokoro

O catálogo original inclui narrações Kokoro pré-geradas; os idiomas incluídos estão descritos em `static/narration/catalog.json`. Elas são servidas como MP3 estáticos e funcionam assim que o site é instalado, sem geração na hospedagem nem ativação manual. O Android também as inclui na exportação. Uma narração personalizada ativada no admin tem prioridade. Se um texto original for editado, a gravação inicial não é aplicada ao texto novo: gere ou envie uma nova narração.

O leitor usa **Narração natural gravada** por padrão: reproduz os MP3 incluídos no catálogo, ficheiros WAV gerados localmente com Kokoro ou uma narração enviada pelo admin (MP3, M4A, OGG ou WAV). Não muda automaticamente para a voz do navegador se faltar uma gravação. Nesse caso, o texto, o temporizador e os sons de fundo continuam disponíveis. A opção **Voz do aparelho** permanece facultativa e deve ser selecionada explicitamente.

Kokoro não exige conta, chave API, créditos ou assinatura. A geração usa o processador e a memória da máquina que executa o servidor. O modelo e as vozes são baixados uma vez; os textos não são enviados a um serviço de síntese. São suportados francês, inglês americano/britânico, italiano, espanhol e português **brasileiro**. A lista do admin mostra apenas vozes compatíveis com o idioma escolhido.

### Preparar localmente

```bash
pip install -r requirements.txt
python3 scripts/prepare_kokoro.py
python3 app.py
```

Os modelos ficam em `models/kokoro/`, excluídos do Git. O script verifica o SHA256 dos dois ficheiros publicados pelo projeto kokoro-onnx antes de os instalar. É seguro repetir a preparação: ficheiros válidos não são baixados novamente. Defina `KOKORO_MODEL_DIR` para usar outro diretório e `KOKORO_THREADS` para limitar os núcleos de CPU (padrão: 2; intervalo: 1–8).

### Docker e administração

O Dockerfile instala o motor CPU e prepara os modelos **durante a construção da imagem**. Basta reconstruir e fazer o deploy; não é necessária nenhuma chave vocal. Os modelos ficam em `/opt/kokoro`, e SQLite/uploads permanecem no volume `/data`. A geração funciona sem conexão depois de a imagem estar preparada. O primeiro carregamento do modelo acontece na tarefa em segundo plano, preservando o arranque e o healthcheck HTTP.

O modelo e as vozes ocupam cerca de 354 MB. Na verificação local com dois threads, o processo atingiu aproximadamente 630 MiB de RAM; reserve pelo menos 1 GiB para o servidor durante a geração. Isso é uso da sua máquina, sem cobrança por caracteres ou minutos. Reproduzir os áudios prontos dispensa o motor.

Na administração, abra **Áudios → Voz natural**, escolha a meditação, idioma, voz Kokoro e ritmo, e clique em **Gerar rascunho de voz**. Cada etapa ou capítulo recebe um WAV mono de 24 kHz separado, mantendo o ritmo do exercício. Escute os trechos e clique em **Usar esta narração** para ativar apenas esse idioma. O upload de narração própria continua disponível.

Os ficheiros ficam em `SEREIN_UPLOADS` e os rascunhos/metadados no SQLite. A mesma geração reutiliza os ficheiros guardados, inclusive os trechos concluídos antes de uma falha. Uma geração com erro não substitui a voz ativa; textos alterados exigem nova geração. Gravações que ultrapassem a duração da etapa não podem ser ativadas: ajuste o ritmo ou o texto e revise novamente. As gravações antigas continuam reproduzíveis; a mudança do motor não apaga áudios nem conteúdos.

Execute apenas um processo Gunicorn, conforme o Dockerfile (com quatro threads), para coordenar as tarefas e o seed SQLite. Reiniciar durante uma geração marca a tarefa como interrompida; tentar novamente reutiliza os trechos guardados. O admin informa se faltam dependências ou modelos. Os testes automáticos usam áudio simulado para cobrir erros e exportação; os exemplos reais em `dist/kokoro-previews/` permitem avaliar o timbre, o sotaque e a naturalidade por idioma antes de publicar.

### Android offline e créditos

Gere e ative os áudios no banco usado na exportação, execute `python3 scripts/export_android_assets.py` e recompile o APK. O exportador inclui os WAV de cada etapa e as informações de licença; o aplicativo instalado apenas reproduz ficheiros locais. O motor e os modelos Kokoro ficam no servidor e não aumentam o APK. Se os dados estiverem hospedados, transfira a base e os uploads para o ambiente de compilação antes de exportar. Os áudios gerados não são enviados automaticamente ao Git.

O modelo Kokoro-82M usa licença Apache 2.0 e o motor kokoro-onnx usa MIT. Os créditos incluem o conjunto SIWIS para a voz francesa. Consulte `licenses/kokoro/` e os créditos do leitor. Referências: [modelo e vozes](https://huggingface.co/hexgrad/Kokoro-82M), [motor ONNX](https://github.com/thewh1teagle/kokoro-onnx).

Para reconstruir as narrações do catálogo original num ambiente de desenvolvimento, instale `requirements-narration-build.txt`, prepare os modelos e execute `python3 scripts/build_narration_seed.py --workers 2`. O processo usa uma base temporária e preserva o banco local. Os WAV intermediários ficam em `models/narration-seed-cache/` para permitir retomar; os MP3 e o manifesto final ficam em `static/narration/`. Cada idioma só entra no manifesto quando todas as suas gravações estiverem concluídas; a atualização é atômica.
