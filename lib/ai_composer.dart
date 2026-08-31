import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'main.dart';

const _apiBaseUrl = String.fromEnvironment(
  'SEREIN_API_URL',
  defaultValue: 'http://10.0.2.2:8080',
);

class AiComposer extends StatefulWidget {
  const AiComposer({super.key, required this.language});
  final Language language;

  @override
  State<AiComposer> createState() => _AiComposerState();
}

class _AiComposerState extends State<AiComposer> {
  final _feeling = TextEditingController();
  String _intention = 'pausa';
  String? _text;
  String? _error;
  bool _loading = false;

  @override
  void dispose() {
    _feeling.dispose();
    super.dispose();
  }

  Future<void> _createPractice() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await http
          .post(
            Uri.parse('$_apiBaseUrl/v1/relaxation-text'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'language': widget.language.name,
              'intention': _intention,
              'feeling': _feeling.text.trim(),
            }),
          )
          .timeout(const Duration(seconds: 20));
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      if (response.statusCode != 200) {
        throw Exception(body['error'] ?? 'Erro inesperado.');
      }
      if (mounted) {
        setState(() => _text = body['text'] as String);
      }
    } catch (error) {
      if (mounted) {
        setState(
          () => _error = error.toString().replaceFirst('Exception: ', ''),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Pausa criada para si')),
    body: ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          'Um texto breve, criado no momento para acompanhar a sua pausa.',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 24),
        Text(
          'O que procura agora?',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        SegmentedButton<String>(
          segments: const [
            ButtonSegment(
              value: 'pausa',
              label: Text('Pausa'),
              icon: Icon(Icons.coffee_outlined),
            ),
            ButtonSegment(
              value: 'respirar',
              label: Text('Respirar'),
              icon: Icon(Icons.air),
            ),
            ButtonSegment(
              value: 'dormir',
              label: Text('Sono'),
              icon: Icon(Icons.nightlight_outlined),
            ),
            ButtonSegment(
              value: 'refletir',
              label: Text('Refletir'),
              icon: Icon(Icons.wb_sunny_outlined),
            ),
          ],
          selected: {_intention},
          onSelectionChanged: (value) =>
              setState(() => _intention = value.first),
        ),
        const SizedBox(height: 24),
        TextField(
          controller: _feeling,
          maxLength: 280,
          maxLines: 3,
          decoration: const InputDecoration(
            labelText: 'Como se sente? (opcional)',
            hintText: 'Ex.: preciso desacelerar depois de um dia intenso',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 10),
        FilledButton.icon(
          onPressed: _loading ? null : _createPractice,
          icon: _loading
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.auto_awesome),
          label: Text(_loading ? 'A criar a sua pausa…' : 'Criar texto'),
        ),
        const SizedBox(height: 18),
        const Text(
          'A IA oferece inspiração para bem-estar; não substitui apoio médico ou psicológico.',
          style: TextStyle(fontSize: 12),
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: 20),
            child: Text(
              _error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        if (_text != null)
          Padding(
            padding: const EdgeInsets.only(top: 20),
            child: Card(
              color: Theme.of(context).colorScheme.secondaryContainer,
              child: Padding(
                padding: const EdgeInsets.all(22),
                child: Text(
                  _text!,
                  style: Theme.of(context).textTheme.bodyLarge
                      ?.copyWith(height: 1.6),
                ),
              ),
            ),
          ),
      ],
    ),
  );
}
