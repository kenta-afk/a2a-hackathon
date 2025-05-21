import argparse
import datetime
import os
from dotenv import load_dotenv
from calendar_agent import CalendarAgent

def main():
    """Main entry point for the Calendar Agent application."""
    # .envファイルから環境変数を読み込む
    load_dotenv()
    
    # 環境変数の確認
    if "CLIENT_ID" not in os.environ:
        print("環境変数 CLIENT_ID が設定されていません。")
        print(".envファイルにCLIENT_ID=your_client_idを追加してください。")
        return
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='Googleカレンダーから予定を取得します。')
    parser.add_argument('--date', '-d', type=str, 
                        help='予定を取得する日付（YYYY-MM-DD形式）。指定がない場合は今日の予定を取得します。')
    args = parser.parse_args()
    
    # 日付の解析または今日の日付を使用
    target_date = None
    if args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"エラー: 日付の形式が不正です。YYYY-MM-DD形式で指定してください。")
            return
    
    print(f"Google Calendar APIを使用してカレンダー予定を取得します...")
    
    try:
        # カレンダーエージェントの初期化
        print("カレンダーエージェントを初期化中...")
        agent = CalendarAgent()
        
        # 指定日付の予定を取得
        date_str = target_date.strftime("%Y-%m-%d") if target_date else "today"
        print(f"{date_str} の予定を取得中...")
        schedule = agent.get_formatted_schedule(target_date)
        
        # 予定の表示
        if schedule:
            print("\nあなたの予定:")
            print("==============")
            for event in schedule:
                print(event)
        else:
            print("\nこの日付には予定がありません。")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
