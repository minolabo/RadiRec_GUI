# RadiRec GUI

radikoの番組を録音するクロスプラットフォーム(Windows/Mac/Linux)対応のGUIツールです。
[rec_radiko_ts.sh](https://github.com/uru2/rec_radiko_ts) (作: uru氏) のロジックがベースです。
radiko側のアップデートにより使えなくなる可能性があります。

radikoタイムフリー、タイムフリー30、エリアフリーに対応しており、30分番組がおおよそ15秒程度で保存できます。
radikoのサービスに干渉するので予約録音や自動保存などの機能はついていません、つける予定もありません。

自分が昔使っていたradikopadという録音ツールに近しいものになっています。

録音したファイルは放送局ごとのフォルダに振り分けて保存されます。

## 必要要件
*   Python 3.x (Windows環境下で.exeを使う場合は不要)
*   ffmpeg 3.x (要AAC,HLSサポート)

## 使い方

### Windows (.exeを使用する場合)
Python環境がなくても動作します。
1. [Releases](https://github.com/minolabo/RadiRec_GUI/releases) から `RadiRec_GUI.exe` をダウンロードして解凍します。
2.  `RadiRec_GUI.exe` を実行してください。
   *   ※同一フォルダ内に `ffmpeg.exe` が必ず必要です。ない場合は下記手順に従ってダウンロードしてください。

### Windows / Mac / Linux (Python環境がある場合)
ソースコードから直接実行します。
1. **ffmpegの準備**:
   *   [ffmpeg公式](https://ffmpeg.org/download.html) からダウンロードし、解凍した `ffmpeg.exe` をスクリプトと同じフォルダに置くか、PATHを通してください。
   *   Mac: `brew install ffmpeg`
   *   Linux: `sudo apt install ffmpeg`
2. **実行**:
   ```bash
   python RadiRec_GUI.py
   # または
   python3 RadiRec_GUI.py
   ```

## 機能説明

### モード
*   **URLから録音**: 番組ページのURL（例: `https://radiko.jp/#!/ts/JORF/20260208000000`）を貼り付けて録音します。
*   **日時指定録音**: 放送局と開始日時、録音時間（分）を手動で指定して録音します。

### 設定・オプション
*   **プレミアムログイン**: エリア外やタイムフリーなどプレミアム会員機能を利用する場合に入力します。
*   **ファイル名規則**: 保存するファイル名のフォーマットを指定できます。
    *   `{DATE}`: 日付 (YYYYMMDD)
    *   `{TIME}`: 時間 (HHMM)
    *   `{TITLE}`: 番組タイトル
    *   `{STATION}`: 放送局ID

## 作者
 minolabo @3939tokai バグ報告などはお気軽にDM飛ばしてください。

## ライセンス
MIT License

Copyright (c) 2026 minolabo
Original Script (rec_radiko_ts.sh) Copyright (c) 2017-2026 uru
