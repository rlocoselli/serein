# Serein — kit de apresentação para Google Play

Preparado em **17/11/2026**, seguindo o formato do kit do Retro Arena. Pacote Android: `io.serein.app`.

## O que já pode ser usado na ficha

- `graphics/icon-512.png`: ícone PNG RGBA de 512 × 512, abaixo de 1 MB, sem cantos recortados ou selo promocional.
- `graphics/feature-<idioma>-1024x500.png`: cinco imagens de destaque PNG RGB de 1024 × 500, sem transparência. Idiomas: pt-BR, en-US, fr-FR, it-IT, es-ES.
- `listings/<idioma>/title.txt`: título de até 30 caracteres.
- `listings/<idioma>/short-description.txt`: descrição curta de até 80 caracteres.
- `listings/<idioma>/full-description.txt`: descrição completa de até 4.000 caracteres.
- `listings/<idioma>/release-notes.txt`: notas de versão de até 500 caracteres.
- `listings/release-notes-play-console.txt`: notas com tags de idioma para copiar no Console.
- `listings/metadata.json`: textos e contagens para automação ou revisão.

As artes são renderizações originais da identidade vetorial existente, com o mascote Lumi. Mantêm a aparência do aplicativo; não foram usadas imagens geradas de uma interface inexistente nem alegações de eficácia clínica.

## Prévias da interface: material de revisão

`previews/` contém **20 capturas web reais da interface compartilhada**, quatro por idioma: início, prática guiada, histórias e sons. Foram obtidas no navegador local, com viewport solicitado de 432 × 768. Os arquivos refletem o enquadramento retornado pelo navegador, em 417 × 741 ou 432 × 768. Não são screenshots de aparelho Android, e o navegador pode incluir barras de rolagem. **Não enviar essas prévias como se fossem screenshots Android.**

Antes de enviar, capturar no APK/AAB de lançamento pelo menos duas screenshots reais de celular, preferencialmente quatro ou mais em 1080 × 1920. Mostrar apenas recursos existentes e conferir cortes, textos, TTS e controles. Não usar dados privados, overlays de depuração ou promessas médicas. As condições de destaque promocional podem exigir dimensões superiores às mínimas.

Sugestão de sequência: tela inicial, exercício com etapas, histórias e fundo sonoro. Para obter uma imagem no aparelho conectado: `adb exec-out screencap -p > screenshot.png`. Validar visualmente antes do upload.

## Política e formulários

- `policy/privacy-policy.html`: página estática em português e inglês, pronta para hospedar após revisão dos dados do responsável. Usa **Audela** e **admin@audeladedonnees.fr**, como no Retro Arena; confirmar que são os dados corretos para este app.
- `policy/play-console-respostas.md`: apoio para Segurança dos dados, acesso, anúncios, público-alvo e declaração de saúde. Não é uma submissão nem uma classificação IARC preenchida.

O aplicativo permanece offline. A **política de privacidade** precisa ter uma URL pública acessível e estar acessível por texto ou link no aplicativo final. Isso não exige transformar o aplicativo em um site público. O HTML preparado ainda não foi hospedado nem incluído no APK atual.

## Antes de enviar a versão de lançamento

1. Atualizar o projeto para **target API 36 ou superior**, exigido para novos apps desde 31/08/2026. O APK de teste entregue anteriormente ainda usa API 35.
2. Gerar e validar **Android App Bundle (.aab) de release**, assinado com chave de upload própria; não enviar o APK debug anterior como release. O kit de ficha não contém chaves ou senhas de assinatura.
3. Testar em Android real: abertura/splash, Voltar, rotação, narração offline nos cinco idiomas, pausa, retorno de segundo plano, vídeos, volume e vibração opcional. Capturar as screenshots do lançamento.
4. Publicar a política, incluir seu acesso no app final e conferir nome/contato do desenvolvedor. O app não deve prometer estimulação clínica do nervo vago, tratamento de ansiedade ou cura de insônia.
5. Preencher os formulários exigidos pelo Console com base no binário final, incluindo funcionalidades de saúde. Confirmar público-alvo, classificação, países e eventuais testes exigidos pela conta.

## Fontes oficiais verificadas

- Assets e descrição: https://support.google.com/googleplay/android-developer/answer/9866151
- Metadados: https://support.google.com/googleplay/android-developer/answer/9859152
- Target API: https://support.google.com/googleplay/android-developer/answer/11926878
- Conteúdo de saúde: https://support.google.com/googleplay/android-developer/answer/16679511
- Segurança dos dados: https://support.google.com/googleplay/android-developer/answer/10787469
- Assinatura: https://developer.android.com/studio/publish/app-signing

Nada foi enviado à Play Console e não há aprovação da loja. Este pacote prepara os materiais da ficha; as etapas acima ainda são necessárias para publicar.
