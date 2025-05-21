# Google Calendar Agent

このプロジェクトは、Google ADKを使用してGoogleカレンダーから予定を取得し、簡潔なフォーマットで表示するエージェントです。

## 機能

- Googleカレンダーから特定の日付（デフォルトは今日）の予定を取得
- 予定を「meeting1 10:00~12:00」の形式で表示

## セットアップ

1. プロジェクトの依存関係をインストール:

```bash
uv install
```

2. 環境変数の設定:

```bash
# LinuxまたはmacOS
export CLIENT_ID=your-google-client-id

# Windows (コマンドプロンプト)
set CLIENT_ID=your-google-client-id

# Windows (PowerShell)
$env:CLIENT_ID = "your-google-client-id"
```

## 使用方法

### 今日の予定を取得

```bash
python3 main.py
```

### 特定の日付の予定を取得

```bash
python3 main.py --date 2025-05-25
```

または短い形式:

```bash
python3 main.py -d 2025-05-25
```

## 出力例

```
Google ADKを使用してカレンダー予定を取得します...
カレンダーエージェントを初期化中...
2025-05-21 の予定を取得中...

あなたの予定:
==============
meeting1 09:00~10:30
meeting2 13:00~14:00
meeting3 15:30~16:30
```

## 技術仕様

- Python 3.13+
- Google ADK 1.0.0+

## 機能拡張の可能性

- 空き時間の検出
- 食事おすすめ機能の統合
- 複数のカレンダー対応
