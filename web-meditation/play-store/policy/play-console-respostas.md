# Respostas de apoio para a Play Console

Referem-se ao APK offline atual `io.serein.app`. Conferir novamente contra o AAB de lançamento; mudanças de SDKs ou recursos podem alterar as respostas. As opções exatas e as obrigações variam conforme o formulário e a conta.

- Desenvolvedor e contato: **Audela**, **admin@audeladedonnees.fr**, reutilizados do material do Retro Arena. Confirmar que este será o responsável pelo Serein.
- Tipo: aplicativo. Categoria sugerida: **Saúde e fitness**, voltado a bem-estar, meditação e relaxamento. Não selecionar tratamento médico, diagnóstico, pesquisa clínica ou integração Health Connect, pois não existem essas funções.
- Público proposto: adultos, 18+. Confirmar a intenção editorial antes de preencher o público-alvo; não marcar dirigido a crianças automaticamente. A classificação IARC deve ser respondida no Console, não presumida a partir deste documento.
- Acesso ao app: todas as funções da versão Android estão acessíveis sem login. O admin Flask é separado e não faz parte da experiência do APK.
- Anúncios: não contém anúncios. Sem compras no app.
- Segurança dos dados: o app atual não coleta nem compartilha dados pessoais fora do aparelho. Idioma e contador permanecem no armazenamento local. TTS usa somente vozes locais sem rede. Sem analytics, IDs publicitários, permissões de saúde, câmera, microfone ou localização. Não confundir o processamento local com transmissão ao desenvolvedor.
- Conta/exclusão: o app não oferece criação de conta. A exclusão de preferências é feita limpando o armazenamento do aplicativo ou desinstalando.
- Permissões: apenas VIBRATE no Manifest; utilizada para pulsos táteis opcionais, sem promessa de estimulação médica do nervo vago.
- Declaração de funcionalidades de saúde: preencher; descrever meditação, relaxamento, atenção plena e visualização guiada para bem-estar. Não afirmar que é um dispositivo médico ou tratamento validado. A descrição completa inclui o caráter não médico e a orientação de consultar profissional de saúde.
- Política de privacidade: o HTML está preparado nesta pasta, mas ainda precisa ser publicado em página pública acessível e também acessível dentro do app final. O funcionamento offline do app não elimina essa exigência de página pública para a política.
- Conteúdo gerado: as histórias são textos originais fixos; não há chatbot ou gerador de conteúdo acessível ao usuário.
- Conteúdo musical: gravações sintetizadas originais CC0, composição de Beethoven em domínio público, créditos preservados em `static/audio/credits.json`. Fontes DejaVu têm licença incluída; Lumi é identidade vetorial própria do projeto.

Fontes verificadas em 17/11/2026:
- https://support.google.com/googleplay/android-developer/answer/10787469 — Segurança dos dados.
- https://support.google.com/googleplay/android-developer/answer/16679511 — Conteúdo e serviços de saúde.
- https://support.google.com/googleplay/android-developer/answer/9866151 — Material visual e descrição da ficha.
