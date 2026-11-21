# Serein

Aplicativo Flutter de meditação, sono e bem-estar. A versão inicial inclui sessões de respiração, textos guiados, vibrações suaves e uma biblioteca preparada para conteúdos privados.

## Deploy da aplicação web

O `Dockerfile` na raiz constrói a aplicação Flask a partir de `web-meditation/`. Na plataforma de hospedagem, selecione a branch `main`, contexto de construção `.` e Dockerfile `Dockerfile`; use o comando de arranque da imagem. O servidor e o healthcheck usam `PORT` (padrão `5000`).

Configure `SEREIN_ADMIN_PASSWORD` e `SEREIN_SECRET_KEY` como segredos da plataforma. Monte um volume persistente em `/data` para guardar SQLite e uploads. A imagem cria o catálogo inicial automaticamente. Para construir localmente, execute `docker build -t serein .`; as instruções completas de execução estão em [web-meditation/README.md](web-meditation/README.md#docker).

A narração natural usa **Kokoro**, sem chave API nem créditos. As narrações iniciais em `web-meditation/static/narration/` são reproduzidas imediatamente, sem geração ou ativação no admin. O manifesto indica os idiomas incluídos e verifica se o texto corresponde à gravação. O português usa vozes brasileiras.

O admin **Áudios → Voz natural** permite gerar e revisar conteúdos personalizados. Estes usam CPU no servidor; os modelos são preparados na construção da imagem Docker. O leitor usa ficheiros de áudio por padrão, sem fallback automático para a voz do navegador. Os áudios também podem ser incluídos no Android offline; o motor e os modelos ficam no servidor.

## Versão web e Android com HTML local

A aplicação web com Flask e SQLite, meditações em cinco idiomas, vídeos, histórias, sons de fundo e administração fica em [web-meditation/](web-meditation/README.md). O projeto Android Studio em [web-meditation/android/](web-meditation/android/README.md) incorpora o HTML e os conteúdos locais para utilização offline.

Consulte o README dessa versão para iniciar o servidor, configurar a administração e gerar o APK. O material de publicação fica em [web-meditation/play-store/](web-meditation/play-store/LEIA-ME.md). As chaves de assinatura, bases locais e compilações geradas não são versionadas.

A branch `web-meditation` mantém estas fontes na raiz para o desenvolvimento independente. Para atualizar esta cópia em `main`, use `git subtree pull --prefix=web-meditation origin web-meditation --squash`.

## Idiomas

Português, francês, italiano e inglês. A opção fica no perfil; o próximo passo editorial é cadastrar cada áudio e texto nos quatro idiomas.

## Executar

```bash
cd /home/locoselli/serein
/home/locoselli/flutter-sdk/bin/flutter pub get
/home/locoselli/flutter-sdk/bin/flutter run
```

## Conteúdo privado

`Serein Plus` é apenas uma demonstração visual nesta primeira versão. A implementação segura de assinatura, validação de recibos e downloads protegidos está descrita em [DRM_E_ASSINATURAS.md](docs/DRM_E_ASSINATURAS.md).

## Textos criados com IA

O aplicativo inclui uma tela de pausa personalizada acessível pelo ícone de brilho na página inicial. O cliente chama um backend Python em `backend/`; a chave da OpenAI fica exclusivamente nesse servidor. Veja as instruções de configuração em [backend/README.md](backend/README.md).

No emulador Android, o endereço padrão é `http://10.0.2.2:8080`. Em produção, defina a URL HTTPS do serviço no build:

```bash
flutter run --dart-define=SEREIN_API_URL=https://api.exemplo.com
```
