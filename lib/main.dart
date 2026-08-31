import 'dart:async';

import 'ai_composer.dart';

import 'package:flutter/material.dart';
import 'package:vibration/vibration.dart';

void main() => runApp(const SereinApp());

enum Language { pt, fr, it, en }

const words = {
  Language.pt: [
    'Um momento para si',
    'Respire devagar. Não há nada para resolver agora.',
    'Começar sessão',
    'Biblioteca',
    'Perfil',
    'Hoje',
    'Sono profundo',
    'Leitura tranquila',
    'Chuva suave',
    'Preferências',
    'Idioma',
    'Privacidade primeiro',
    'Sem conta obrigatória para explorar os conteúdos gratuitos.',
    'Serein Plus',
    'Ativar demonstração',
    'Assinatura ativa',
    'A sua prática de hoje',
    'Sessão concluída',
  ],
  Language.fr: [
    'Un instant pour vous',
    'Respirez lentement. Il n’y a rien à résoudre maintenant.',
    'Commencer la séance',
    'Bibliothèque',
    'Profil',
    'Aujourd’hui',
    'Sommeil profond',
    'Lecture apaisante',
    'Pluie douce',
    'Préférences',
    'Langue',
    'Votre vie privée avant tout',
    'Aucun compte n’est nécessaire pour découvrir les contenus gratuits.',
    'Serein Plus',
    'Activer la démo',
    'Abonnement actif',
    'Votre pratique du jour',
    'Séance terminée',
  ],
  Language.it: [
    'Un momento per te',
    'Respira lentamente. Ora non c’è nulla da risolvere.',
    'Inizia la sessione',
    'Libreria',
    'Profilo',
    'Oggi',
    'Sonno profondo',
    'Lettura tranquilla',
    'Pioggia leggera',
    'Preferenze',
    'Lingua',
    'La privacy prima di tutto',
    'Nessun account richiesto per esplorare i contenuti gratuiti.',
    'Serein Plus',
    'Attiva la demo',
    'Abbonamento attivo',
    'La tua pratica di oggi',
    'Sessione conclusa',
  ],
  Language.en: [
    'A moment for you',
    'Breathe slowly. There is nothing to solve right now.',
    'Start session',
    'Library',
    'Profile',
    'Today',
    'Deep sleep',
    'Quiet reading',
    'Soft rain',
    'Preferences',
    'Language',
    'Privacy first',
    'No account is required to explore free content.',
    'Serein Plus',
    'Activate demo',
    'Membership active',
    'Your practice today',
    'Session complete',
  ],
};

class SereinApp extends StatefulWidget {
  const SereinApp({super.key});
  @override
  State<SereinApp> createState() => _SereinAppState();
}

class _SereinAppState extends State<SereinApp> {
  Language language = Language.pt;
  bool plus = false;
  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    title: 'Serein',
    theme: ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: const Color(0xffFBFAF6),
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xff536C60),
        surface: const Color(0xffFBFAF6),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      ),
    ),
    home: Shell(
      language: language,
      plus: plus,
      onLanguage: (v) => setState(() => language = v),
      onUnlock: () => setState(() => plus = true),
    ),
  );
}

class Shell extends StatefulWidget {
  const Shell({
    super.key,
    required this.language,
    required this.plus,
    required this.onLanguage,
    required this.onUnlock,
  });
  final Language language;
  final bool plus;
  final ValueChanged<Language> onLanguage;
  final VoidCallback onUnlock;
  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  int selected = 0;
  @override
  Widget build(BuildContext context) {
    final w = words[widget.language]!;
    final pages = [
      Today(language: widget.language),
      Library(
        language: widget.language,
        plus: widget.plus,
        onUnlock: widget.onUnlock,
      ),
      Profile(language: widget.language, onLanguage: widget.onLanguage),
    ];
    return Scaffold(
      body: SafeArea(child: pages[selected]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: selected,
        onDestinationSelected: (v) => setState(() => selected = v),
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.spa_outlined),
            selectedIcon: const Icon(Icons.spa),
            label: w[5],
          ),
          NavigationDestination(
            icon: const Icon(Icons.auto_stories_outlined),
            selectedIcon: const Icon(Icons.auto_stories),
            label: w[3],
          ),
          NavigationDestination(
            icon: const Icon(Icons.person_outline),
            selectedIcon: const Icon(Icons.person),
            label: w[4],
          ),
        ],
      ),
    );
  }
}

class Today extends StatelessWidget {
  const Today({super.key, required this.language});
  final Language language;
  @override
  Widget build(BuildContext context) {
    final w = words[language]!;
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 18, 24, 32),
      children: [
        Row(
          children: [
            Image.asset(
              'assets/branding/serein-logo.png',
              width: 42,
              height: 42,
            ),
            const SizedBox(width: 12),
            Text(
              'Serein',
              style: Theme.of(context).textTheme.titleLarge
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const Spacer(),
            IconButton(
              tooltip: 'Criar uma pausa com IA',
              icon: const Icon(Icons.auto_awesome_outlined),
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => AiComposer(language: language),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 42),
        Text(
          w[0],
          style: Theme.of(context).textTheme.displaySmall
              ?.copyWith(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 10),
        Text(
          w[1],
          style: Theme.of(context).textTheme.titleMedium
              ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
        ),
        const SizedBox(height: 32),
        Text(
          w[16],
          style: Theme.of(context).textTheme.titleMedium
              ?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 12),
        Featured(language: language),
        const SizedBox(height: 28),
        Text(
          w[3],
          style: Theme.of(context).textTheme.titleMedium
              ?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 12),
        SessionTile(
          language: language,
          icon: Icons.nightlight_round,
          title: w[6],
          detail: '20 min · áudio + vibração',
          locked: true,
        ),
        const SizedBox(height: 10),
        SessionTile(
          language: language,
          icon: Icons.menu_book_outlined,
          title: w[7],
          detail: '7 min · texto guiado',
          locked: false,
        ),
      ],
    );
  }
}

class Featured extends StatelessWidget {
  const Featured({super.key, required this.language});
  final Language language;
  @override
  Widget build(BuildContext context) {
    final w = words[language]!;
    return Material(
      color: const Color(0xffDDE9DC),
      borderRadius: BorderRadius.circular(28),
      child: InkWell(
        borderRadius: BorderRadius.circular(28),
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => Session(language: language)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.air_rounded, size: 34),
              const SizedBox(height: 30),
              Text(
                'Respiração 4–6',
                style: Theme.of(context).textTheme.headlineSmall
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 6),
              Text(w[1]),
              const SizedBox(height: 22),
              const Row(
                children: [
                  Text('5 min'),
                  Spacer(),
                  CircleAvatar(
                    backgroundColor: Color(0xff536C60),
                    foregroundColor: Colors.white,
                    child: Icon(Icons.play_arrow_rounded),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class SessionTile extends StatelessWidget {
  const SessionTile({
    super.key,
    required this.language,
    required this.icon,
    required this.title,
    required this.detail,
    required this.locked,
  });
  final Language language;
  final IconData icon;
  final String title, detail;
  final bool locked;
  @override
  Widget build(BuildContext context) => Card(
    color: Theme.of(context).colorScheme.surfaceContainerLowest,
    child: ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
      leading: CircleAvatar(
        backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
        child: Icon(icon),
      ),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text(detail),
      trailing: Icon(
        locked ? Icons.lock_outline_rounded : Icons.play_circle_outline_rounded,
      ),
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) =>
              Session(language: language, locked: locked, title: title),
        ),
      ),
    ),
  );
}

class Session extends StatefulWidget {
  const Session({
    super.key,
    required this.language,
    this.locked = false,
    this.title,
  });
  final Language language;
  final bool locked;
  final String? title;
  @override
  State<Session> createState() => _SessionState();
}

class _SessionState extends State<Session> {
  Timer? timer;
  int seconds = 300;
  bool running = false;
  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  void toggle() {
    if (running) {
      timer?.cancel();
      setState(() => running = false);
      return;
    }
    setState(() => running = true);
    timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (seconds <= 1) {
        timer?.cancel();
        setState(() {
          seconds = 0;
          running = false;
        });
      } else {
        setState(() => seconds--);
      }
    });
    Vibration.hasVibrator().then((v) {
      if (v == true) Vibration.vibrate(duration: 70, amplitude: 50);
    });
  }

  @override
  Widget build(BuildContext context) {
    final w = words[widget.language]!;
    if (widget.locked) {
      return Scaffold(
        appBar: AppBar(),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.lock_outline_rounded,
                size: 56,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 16),
              Text(
                w[13],
                style: Theme.of(context).textTheme.headlineSmall
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              const Text(
                'Este conteúdo é reservado a membros com assinatura ativa.',
              ),
            ],
          ),
        ),
      );
    }
    final time =
        '${(seconds ~/ 60).toString().padLeft(2, '0')}:${(seconds % 60).toString().padLeft(2, '0')}';
    return Scaffold(
      appBar: AppBar(title: Text(widget.title ?? 'Respiração 4–6')),
      body: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          children: [
            const Spacer(),
            Container(
              width: 230,
              height: 230,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xffDDE9DC),
                border: Border.all(color: const Color(0xffA9C1AB), width: 2),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    seconds == 0 ? w[17] : time,
                    style: Theme.of(context).textTheme.displaySmall
                        ?.copyWith(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    running ? w[1] : 'Respiração 4–6',
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
            const Spacer(),
            FilledButton.icon(
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(56),
              ),
              onPressed: seconds == 0
                  ? () => setState(() => seconds = 300)
                  : toggle,
              icon: Icon(
                running ? Icons.pause_rounded : Icons.play_arrow_rounded,
              ),
              label: Text(seconds == 0 ? w[2] : (running ? 'Pausar' : w[2])),
            ),
          ],
        ),
      ),
    );
  }
}

class Library extends StatelessWidget {
  const Library({
    super.key,
    required this.language,
    required this.plus,
    required this.onUnlock,
  });
  final Language language;
  final bool plus;
  final VoidCallback onUnlock;
  @override
  Widget build(BuildContext context) {
    final w = words[language]!;
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          w[3],
          style: Theme.of(context).textTheme.displaySmall
              ?.copyWith(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 10),
        const Text(
          'Práticas para desacelerar, descansar e voltar ao seu centro.',
        ),
        const SizedBox(height: 28),
        SessionTile(
          language: language,
          icon: Icons.water_drop_outlined,
          title: w[8],
          detail: '30 min · áudio',
          locked: false,
        ),
        const SizedBox(height: 16),
        Card(
          color: Theme.of(context).colorScheme.secondaryContainer,
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.workspace_premium_outlined),
                const SizedBox(height: 14),
                Text(
                  w[13],
                  style: Theme.of(context).textTheme.headlineSmall
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Sons para dormir, programas de 7 dias e leituras completas.',
                ),
                const SizedBox(height: 18),
                FilledButton(
                  onPressed: plus ? null : onUnlock,
                  child: Text(plus ? w[15] : w[14]),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class Profile extends StatelessWidget {
  const Profile({super.key, required this.language, required this.onLanguage});
  final Language language;
  final ValueChanged<Language> onLanguage;
  @override
  Widget build(BuildContext context) {
    final w = words[language]!;
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          w[9],
          style: Theme.of(context).textTheme.displaySmall
              ?.copyWith(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 28),
        Text(
          w[10],
          style: Theme.of(context).textTheme.titleMedium
              ?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<Language>(
          initialValue: language,
          decoration: const InputDecoration(border: OutlineInputBorder()),
          onChanged: (v) {
            if (v != null) onLanguage(v);
          },
          items: const [
            DropdownMenuItem(value: Language.pt, child: Text('Português')),
            DropdownMenuItem(value: Language.fr, child: Text('Français')),
            DropdownMenuItem(value: Language.it, child: Text('Italiano')),
            DropdownMenuItem(value: Language.en, child: Text('English')),
          ],
        ),
        const SizedBox(height: 30),
        Card(
          child: ListTile(
            contentPadding: const EdgeInsets.all(20),
            leading: const Icon(Icons.privacy_tip_outlined),
            title: Text(
              w[11],
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(w[12]),
            ),
          ),
        ),
      ],
    );
  }
}
