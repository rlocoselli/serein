import 'package:flutter_test/flutter_test.dart';
import 'package:serein/main.dart';

void main() {
  testWidgets('shows the Serein welcome screen', (tester) async {
    await tester.pumpWidget(const SereinApp());

    expect(find.text('Serein'), findsOneWidget);
    expect(find.text('Um momento para si'), findsOneWidget);
    expect(find.text('Respiração 4–6'), findsOneWidget);
  });
}
