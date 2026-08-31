# Serein

Aplicativo Flutter de meditação, sono e bem-estar. A versão inicial inclui sessões de respiração, textos guiados, vibrações suaves e uma biblioteca preparada para conteúdos privados.

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
