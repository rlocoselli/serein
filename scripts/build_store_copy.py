"""Store copy describes shipped functionality, without clinical efficacy claims."""
from pathlib import Path
import json,html
OUT=Path('play-store');meta={}
copy={
'pt-BR':('Serein: meditação e histórias','Meditações, histórias e sons para criar suas pausas, mesmo sem conexão', '''Reserve um momento para respirar, ouvir uma história e voltar ao presente. Serein reúne práticas guiadas, visualizações imaginadas e paisagens sonoras em uma experiência tranquila, acompanhada por Lumi.

ESCOLHA A SUA PAUSA
• Respiração suave com orientação visual opcional.
• Relaxamento muscular progressivo em uma adaptação breve.
• Introdução à atenção plena, com respiração natural.
• Meditações de relaxamento e preparação para o descanso.

HISTÓRIAS COM FUNDO SONORO
Conheça A enseada tranquila e O jardim depois da chuva. São histórias originais de visualização guiada, inspiradas em práticas de relaxamento usadas na sofrologia, com capítulos e pausas para observar suas próprias sensações.

UM AMBIENTE PARA OUVIR
Escolha mar suave, chuva leve ou um arranjo sintetizado do tema Ode à Alegria, de Beethoven. Ajuste o fundo separadamente da voz. As vibrações suaves são opcionais e funcionam como marcadores táteis durante a prática.

NO SEU IDIOMA, NO SEU APARELHO
O conteúdo está disponível em português, inglês, francês, italiano e espanhol. Textos, vídeos e fundos sonoros ficam incluídos no aplicativo e funcionam sem conexão. A narração usa a síntese de voz do Android e exige uma voz offline instalada no idioma escolhido.

SEM CONTA, SEM ANÚNCIOS
Não é necessário criar conta. O aplicativo não inclui anúncios, analytics ou compras. A preferência de idioma e o contador de sessões concluídas ficam no aparelho.

FONTES E LIMITES CLAROS
As práticas apresentam referências de serviços de saúde e explicam suas adaptações. Os exercícios e as histórias desta aplicação não foram validados clinicamente. Serein é um recurso de bem-estar, não um dispositivo médico: não diagnostica, trata, cura ou previne condições de saúde. Não substitui aconselhamento, diagnóstico ou tratamento profissional. Consulte um profissional qualificado para questões de saúde. As vibrações do celular não são estimulação médica do nervo vago. Interrompa a prática se houver desconforto.''', 'Primeira versão do Serein: meditações guiadas, duas histórias com fundo sonoro, vídeos, cinco idiomas, música de Beethoven e vibrações opcionais. Conteúdo incluído no app; narração com voz offline instalada no Android.'),
'en-US':('Serein: meditation and stories','Guided practices, stories and soundscapes for your pauses, even offline', '''Make space to breathe, listen to a story and return to the present. Serein brings guided practices, imagined journeys and soundscapes into a gentle experience with Lumi.

CHOOSE A PAUSE
• Gentle breathing with optional visual pacing.
• A brief adaptation of progressive muscle relaxation.
• An introduction to mindfulness with natural breathing.
• Relaxation meditations and wind-down sessions.

STORIES WITH SOUNDSCAPES
Explore The quiet cove and The garden after the rain. These original guided imagery stories draw on relaxation practices used in sophrology, with chapters and pauses to notice your own sensations.

A LANDSCAPE TO LISTEN TO
Choose a soft ocean, gentle rain or an original synthetic arrangement of Beethoven’s Ode to Joy theme. Adjust the background separately from narration. Optional gentle vibrations provide tactile cues during practice.

YOUR LANGUAGE, YOUR DEVICE
Content is available in Portuguese, English, French, Italian and Spanish. Text, videos and background sounds are bundled with the app and work offline. Narration uses Android text-to-speech and requires an installed offline voice for your chosen language.

NO ACCOUNT OR ADS
No account is required. The app contains no ads, analytics or purchases. Your language preference and completed-session count stay on your device.

CLEAR SOURCES AND LIMITS
Practices include health-service references and explain their adaptations. These app exercises and stories have not been clinically validated. Serein is a wellbeing tool, not a medical device: it does not diagnose, treat, cure or prevent health conditions. It does not replace professional advice, diagnosis or treatment. Consult a qualified professional about health concerns. Phone vibrations are not medical vagus nerve stimulation. Stop if you feel uncomfortable.''', 'Welcome to Serein: guided practices, two stories with soundscapes, videos, five languages, Beethoven music and optional vibrations. Content is included in the app; narration requires an installed Android offline voice.'),
'fr-FR':('Serein : méditation et récits','Méditations, histoires et ambiances sonores pour vos pauses, même hors ligne', '''Prenez le temps de respirer, d’écouter une histoire et de retrouver le présent. Serein réunit des pratiques guidées, des voyages imaginés et des ambiances sonores dans un espace apaisant, avec Lumi.

CHOISISSEZ VOTRE PAUSE
• Respiration douce avec un rythme visuel facultatif.
• Adaptation brève de la relaxation musculaire progressive.
• Introduction à la pleine conscience avec respiration naturelle.
• Méditations de détente et préparation au repos.

DES HISTOIRES À ÉCOUTER
Découvrez La crique paisible et Le jardin après la pluie. Ces histoires originales de visualisation guidée s’inspirent de pratiques de relaxation utilisées en sophrologie, avec des chapitres et des pauses pour observer vos sensations.

VOTRE AMBIANCE SONORE
Choisissez la mer, une pluie légère ou un arrangement synthétisé original du thème de l’Ode à la joie de Beethoven. Réglez le fond séparément de la voix. Des vibrations douces et facultatives offrent des repères tactiles pendant la pratique.

CINQ LANGUES, SANS CONNEXION
Les contenus sont disponibles en portugais, anglais, français, italien et espagnol. Textes, vidéos et sons sont inclus dans l’application. La narration utilise la synthèse vocale Android et nécessite une voix hors ligne installée dans la langue choisie.

SANS COMPTE NI PUBLICITÉ
Aucun compte n’est nécessaire. L’application ne contient ni publicité, ni service d’analyse, ni achat. La langue choisie et le compteur de séances terminées restent sur l’appareil.

DES SOURCES ET DES LIMITES EXPLICITES
Les pratiques présentent leurs références de services de santé et leurs adaptations. Ces exercices et histoires n’ont pas été validés cliniquement. Serein est un outil de bien-être, pas un dispositif médical : il ne diagnostique, ne traite, ne guérit et ne prévient aucune affection. Il ne remplace pas un avis, un diagnostic ou un traitement professionnel. Consultez un professionnel qualifié pour vos questions de santé. Les vibrations du téléphone ne constituent pas une stimulation médicale du nerf vague. Arrêtez en cas de gêne.''', 'Première version de Serein : pratiques guidées, deux histoires avec fond sonore, vidéos, cinq langues, musique de Beethoven et vibrations facultatives. Contenu inclus ; voix Android hors ligne installée nécessaire pour la narration.'),
'it-IT':('Serein: meditazione e storie','Meditazioni, storie e suoni per le tue pause, anche senza connessione', '''Prenditi un momento per respirare, ascoltare una storia e tornare al presente. Serein unisce pratiche guidate, viaggi immaginati e paesaggi sonori in un’esperienza tranquilla con Lumi.

SCEGLI LA TUA PAUSA
• Respiro dolce con guida visiva facoltativa.
• Breve adattamento del rilassamento muscolare progressivo.
• Introduzione alla mindfulness con respiro naturale.
• Meditazioni di rilassamento e preparazione al riposo.

STORIE CON SUONI DI FONDO
Scopri La baia tranquilla e Il giardino dopo la pioggia. Sono storie originali di visualizzazione guidata, ispirate a pratiche di rilassamento usate in sofrologia, con capitoli e pause per osservare le tue sensazioni.

UN PAESAGGIO DA ASCOLTARE
Scegli il mare, una pioggia lieve o un arrangiamento sintetizzato originale del tema dell’Inno alla gioia di Beethoven. Regola il fondo separatamente dalla voce. Le vibrazioni delicate e facoltative offrono segnali tattili durante la pratica.

CINQUE LINGUE, SENZA CONNESSIONE
I contenuti sono disponibili in portoghese, inglese, francese, italiano e spagnolo. Testi, video e suoni sono inclusi nell’app. La narrazione usa la sintesi vocale Android e richiede una voce offline installata per la lingua scelta.

SENZA ACCOUNT O PUBBLICITÀ
Non occorre un account. L’app non contiene pubblicità, strumenti di analisi o acquisti. La lingua scelta e il contatore delle sessioni completate restano sul dispositivo.

FONTI E LIMITI CHIARI
Le pratiche indicano fonti sanitarie e spiegano gli adattamenti. Gli esercizi e le storie dell’app non sono stati validati clinicamente. Serein è uno strumento di benessere, non un dispositivo medico: non diagnostica, tratta, cura o previene condizioni di salute. Non sostituisce consigli, diagnosi o trattamenti professionali. Consulta un professionista qualificato per questioni di salute. Le vibrazioni del telefono non sono stimolazione medica del nervo vago. Interrompi in caso di disagio.''', 'Prima versione di Serein: pratiche guidate, due storie con suoni di fondo, video, cinque lingue, musica di Beethoven e vibrazioni facoltative. Contenuti inclusi; la narrazione richiede una voce offline Android installata.'),
'es-ES':('Serein: meditación e historias','Meditaciones, historias y sonidos para tus pausas, incluso sin conexión', '''Dedica un momento a respirar, escuchar una historia y volver al presente. Serein reúne prácticas guiadas, viajes imaginados y paisajes sonoros en una experiencia tranquila con Lumi.

ELIGE TU PAUSA
• Respiración suave con ritmo visual opcional.
• Adaptación breve de la relajación muscular progresiva.
• Introducción a la atención plena con respiración natural.
• Meditaciones de relajación y preparación para el descanso.

HISTORIAS CON SONIDO DE FONDO
Descubre La cala tranquila y El jardín después de la lluvia. Son historias originales de visualización guiada, inspiradas en prácticas de relajación utilizadas en sofrología, con capítulos y pausas para observar tus sensaciones.

UN PAISAJE PARA ESCUCHAR
Elige mar suave, lluvia ligera o un arreglo sintetizado original del tema de la Oda a la alegría de Beethoven. Ajusta el fondo por separado de la voz. Las vibraciones suaves opcionales ofrecen señales táctiles durante la práctica.

CINCO IDIOMAS, SIN CONEXIÓN
Hay contenido en portugués, inglés, francés, italiano y español. Textos, vídeos y sonidos están incluidos en la aplicación. La narración usa la síntesis de voz de Android y requiere una voz sin conexión instalada para el idioma elegido.

SIN CUENTA NI ANUNCIOS
No necesitas crear una cuenta. La aplicación no contiene anuncios, servicios de análisis ni compras. El idioma y el contador de sesiones completadas permanecen en tu dispositivo.

FUENTES Y LÍMITES CLAROS
Las prácticas muestran sus referencias sanitarias y explican las adaptaciones. Los ejercicios y las historias de esta aplicación no se han validado clínicamente. Serein es una herramienta de bienestar, no un dispositivo médico: no diagnostica, trata, cura ni previene condiciones de salud. No sustituye el consejo, diagnóstico o tratamiento profesional. Consulta a un profesional cualificado para cuestiones de salud. Las vibraciones del teléfono no son estimulación médica del nervio vago. Detén la práctica si sientes malestar.''', 'Primera versión de Serein: prácticas guiadas, dos historias con sonido de fondo, vídeos, cinco idiomas, música de Beethoven y vibraciones opcionales. Contenidos incluidos; la narración requiere una voz Android sin conexión instalada.')}
for locale,(title,short,full,notes) in copy.items():
 assert len(title)<=30,(locale,len(title));assert len(short)<=80;assert len(full)<=4000;assert len(notes)<=500
 directory=OUT/'listings'/locale;directory.mkdir(parents=True,exist_ok=True)
 for name,text in [('title',title),('short-description',short),('full-description',full),('release-notes',notes)]: (directory/(name+'.txt')).write_text(text+'\n')
 meta[locale]={'title':title,'short_description':short,'full_description':full,'release_notes':notes,'lengths':{'title':len(title),'short_description':len(short),'full_description':len(full)}}
(OUT/'listings/metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
(OUT/'listings/release-notes-play-console.txt').write_text('\n'.join(f'<{l}>\n{v[3]}\n</{l}>' for l,v in copy.items())+'\n')
print('Validated titles, short/full descriptions and release notes in five locales')
