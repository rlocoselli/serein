# Serein Android — HTML empacotado, sem servidor

Abra esta pasta no Android Studio. Requisitos: JDK 17, Android SDK 35 e Build Tools 35.0.0. O Gradle Wrapper 8.9 está incluído; a primeira sincronização do ambiente de desenvolvimento pode baixar as dependências de compilação. O aplicativo instalado não precisa de rede.

O APK usa exatamente o HTML/CSS/JS de `../static`, copiado em `app/src/main/assets/web`. As leituras de `/api/sessions` e `/api/music` são interceptadas dentro do WebView e resolvidas a partir do catálogo JSON local. O domínio `appassets.androidplatform.net` é apenas uma origem virtual interceptada localmente; não é um site hospedado. O Manifest não declara INTERNET. A navegação externa é bloqueada.

Para atualizar os conteúdos publicados do banco local e recompilar:

```bash
cd ..
python3 scripts/export_android_assets.py
cd android
./gradlew assembleDebug
```

Também existe compilação direta com as ferramentas do SDK, usada para gerar o APK entregue:

```bash
python3 scripts/build_apk.py
```

Saída: `../dist/serein-variety-debug.apk`. É uma versão de desenvolvimento assinada com chave debug. Para distribuição em loja, configure uma chave de release própria. A chave usada nesta máquina fica em `../.local-signing/serein-debug.jks`, fora do projeto. Preserve sua chave se quiser instalar futuras atualizações sobre esta versão; o Gradle pode usar outra chave debug.

A narração prioriza ficheiros de áudio incluídos no APK. A opção facultativa Voz do aparelho usa apenas vozes Android instaladas que não exigem rede. Se não houver gravação nem voz instalada, os textos continuam disponíveis. O aplicativo instalado não envia texto a serviços TTS na nuvem; a geração Kokoro descrita abaixo acontece no servidor, antes de exportar os conteúdos.

As vibrações estão desativadas inicialmente. Quando habilitadas pelo usuário, emitem pulsos curtos na sessão e cessam ao pausar, concluir ou sair de primeiro plano. Não oferecem estimulação médica do nervo vago. Respeite as preferências e o conforto do usuário; suporte e intensidade dependem do aparelho.

O admin permanece no servidor Flask local. Para atualizar o catálogo do APK, edite ou envie mídias no admin e execute a exportação e a compilação novamente. O APK não contém credenciais de administração nem banco SQLite. As histórias são adaptações originais de visualização guiada e não protocolos clínicos de sofrologia.

Verificado: compilação Java/DEX e recursos Android, assinatura APK v2/v3, Manifest com apenas VIBRATE, catálogos e arquivos empacotados, API e reprodução do fundo sonoro no navegador. Sem emulador instalado: reprodução, voz, splash e vibração nativos ainda precisam de teste em aparelho Android real.

## Catálogo ampliado — versão 1.1.0 (2)

São 16 sessões nos cinco idiomas, incluindo 11 práticas estruturadas. As oito adições oferecem manhã, trabalho, escuta, varredura corporal, autocompaixão, emoções, descanso noturno e caminhada consciente. Busca ignora acentos e combina categoria com duração.

A chave debug temporária da versão antiga não estava mais disponível. Esta compilação recebeu uma nova assinatura de teste, guardada em `.local-signing/` e excluída do controle de versão e dos ZIPs. Se o APK antigo estiver instalado com assinatura diferente, o Android recusará a atualização direta. Desinstalar a versão anterior apaga as preferências e o contador locais; faça isso somente se quiser substituir essa instalação de teste. A versão anterior do APK permanece em `dist/serein-debug.apk`.

## Voz e sons — versão 1.2.0 (3)

O APK mais recente é `dist/serein-calm-audio-debug.apk` (caminho relativo à raiz do repositório), com dez sons estéreo e preferências de voz. A versão usa a mesma chave debug persistida da versão 1.1.0. O bridge só lista vozes offline do idioma escolhido e permite configurar velocidade, tom e volume. Cada frase tem um identificador; callbacks de falas canceladas não iniciam a frase seguinte.

Validações desta versão: testes do sequenciador e do catálogo, integridade/RMS/picos/junção dos dez loops, compilação Java/DEX, assinatura APK e controles/reprodução de fundo no navegador. A escolha e a naturalidade das vozes nativas precisam ser verificadas em aparelho com vozes offline instaladas; não houve teste auditivo de TTS Android neste ambiente.

## Narração natural pré-gravada

O leitor prioriza os ficheiros de narração, sem fallback automático para TTS. As 16 sessões iniciais incluem MP3 Kokoro nos cinco idiomas. Para conteúdos personalizados, gere e ative cada idioma no admin Flask, ou envie uma narração própria, antes de exportar os assets. `scripts/export_android_assets.py` copia os MP3 iniciais e os WAV publicados de cada etapa do protocolo para o APK. A geração Kokoro acontece localmente no servidor, sem conta ou chave API; o aplicativo continua sem permissão de internet e não inclui o motor nem os modelos. A voz do aparelho permanece uma opção explícita. Consulte a configuração em [../README.md](../README.md#narração-natural-gratuita-com-kokoro).
