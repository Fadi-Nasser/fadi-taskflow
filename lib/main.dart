import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fadi TaskFlow',
      home: Scaffold(
        body: SafeArea(
          child: WebView(
            initialUrl: 'https://your-flet-app.vercel.app', // ✨ استبدل هذا بالرابط الفعلي لتطبيقك
            javascriptMode: JavascriptMode.unrestricted,
          ),
        ),
      ),
    );
  }
}
