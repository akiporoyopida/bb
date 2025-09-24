#!/usr/bin/env python3
"""
Claude Code使用実績ターミナルビューアー
ccusage blocks --json の出力を解析してタイムラインを表示

使用例:
    ccusage blocks --json | python3 claude_code_viewer.py          # パイプで入力
    python3 claude_code_viewer.py < blocks.json                    # ファイルから入力
    python3 claude_code_viewer.py --file blocks.json               # ファイル指定
    python3 claude_code_viewer.py --high-cost                      # 高コスト日のみ
    python3 claude_code_viewer.py --sort-cost --limit 10           # コスト順TOP10
"""

import json
import sys
import datetime
import argparse
from dataclasses import dataclass
from typing import List, Dict, Optional
import locale

# 日本語表示のためのロケール設定
try:
    locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
except:
    pass

@dataclass
class Block:
    id: str
    start_time: str
    end_time: str
    actual_end_time: Optional[str]
    is_active: bool
    is_gap: bool
    entries: int
    total_tokens: int
    cost_usd: float
    models: List[str]
    duration_minutes: int = 0

class ClaudeCodeViewer:
    def __init__(self, no_color: bool = False):
        self.blocks = []
        self.daily_data = {}
        self.no_color = no_color
        
        # ターミナルカラー
        if no_color:
            self.COLORS = {key: '' for key in ['HEADER', 'BLUE', 'GREEN', 'YELLOW', 
                                                'RED', 'ENDC', 'BOLD', 'UNDERLINE', 
                                                'CYAN', 'WHITE', 'GRAY', 'MAGENTA']}
        else:
            self.COLORS = {
                'HEADER': '\033[95m',
                'BLUE': '\033[94m',
                'GREEN': '\033[92m',
                'YELLOW': '\033[93m',
                'RED': '\033[91m',
                'ENDC': '\033[0m',
                'BOLD': '\033[1m',
                'UNDERLINE': '\033[4m',
                'CYAN': '\033[96m',
                'WHITE': '\033[97m',
                'GRAY': '\033[90m',
                'MAGENTA': '\033[95m',
            }
        
        # アスキーアートバー文字
        self.BAR_CHARS = {
            'opus': '█',
            'sonnet': '▓',
            'mixed': '▒',
            'synthetic': '░',
            'empty': '·',
            'hour_mark': '│',
        }

    def load_from_json(self, json_data: Dict):
        """JSONデータからブロックを読み込み"""
        self.blocks = []
        
        for block_data in json_data.get('blocks', []):
            if block_data['isGap']:
                continue
                
            # 時間を解析
            start_time = datetime.datetime.fromisoformat(block_data['startTime'].replace('Z', '+00:00'))
            
            if block_data['actualEndTime']:
                end_time = datetime.datetime.fromisoformat(block_data['actualEndTime'].replace('Z', '+00:00'))
            else:
                end_time = datetime.datetime.fromisoformat(block_data['endTime'].replace('Z', '+00:00'))
            
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            
            # モデル名を簡略化
            models = []
            for model in block_data['models']:
                if 'opus' in model:
                    models.append('opus-4')
                elif 'sonnet' in model:
                    models.append('sonnet-4')
                elif 'synthetic' in model:
                    models.append('synthetic')
                else:
                    models.append(model)
            
            block = Block(
                id=block_data['id'],
                start_time=start_time.strftime('%Y-%m-%d %H:%M'),
                end_time=end_time.strftime('%Y-%m-%d %H:%M'),
                actual_end_time=block_data['actualEndTime'],
                is_active=block_data['isActive'],
                is_gap=block_data['isGap'],
                entries=block_data['entries'],
                total_tokens=block_data['totalTokens'],
                cost_usd=block_data['costUSD'],
                models=list(set(models)),  # 重複を削除
                duration_minutes=duration_minutes
            )
            
            self.blocks.append(block)
        
        # 日付ごとにグループ化
        self._group_by_date()

    def _group_by_date(self):
        """日付ごとにブロックをグループ化"""
        self.daily_data = {}
        
        for block in self.blocks:
            date_str = block.start_time.split(' ')[0]
            
            if date_str not in self.daily_data:
                self.daily_data[date_str] = {
                    'blocks': [],
                    'total_duration': 0,
                    'total_cost': 0,
                    'total_tokens': 0,
                    'total_entries': 0,
                    'models': set()
                }
            
            self.daily_data[date_str]['blocks'].append(block)
            self.daily_data[date_str]['total_duration'] += block.duration_minutes
            self.daily_data[date_str]['total_cost'] += block.cost_usd
            self.daily_data[date_str]['total_tokens'] += block.total_tokens
            self.daily_data[date_str]['total_entries'] += block.entries
            
            for model in block.models:
                self.daily_data[date_str]['models'].add(model)

    def _get_weekday(self, date_str: str) -> str:
        """曜日を取得"""
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return weekdays[date.weekday()]

    def _format_number(self, num: int) -> str:
        """数値をカンマ区切りで表示"""
        return f"{num:,}"

    def _get_timeline_bar(self, blocks: List[Block], width: int = 48) -> str:
        """24時間のタイムラインバーを生成"""
        # 48文字で24時間を表現（1文字 = 30分）
        timeline = [self.BAR_CHARS['empty']] * width
        
        for block in blocks:
            # 開始時刻を解析
            time_parts = block.start_time.split(' ')[1].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            start_pos = int((hour * 60 + minute) / 30)  # 30分単位
            duration_blocks = max(1, int(block.duration_minutes / 30))
            
            # モデルに応じてバーの文字を決定
            if len(block.models) > 1:
                bar_char = self.BAR_CHARS['mixed']
            elif 'synthetic' in block.models[0]:
                bar_char = self.BAR_CHARS['synthetic']
            elif 'sonnet' in block.models[0]:
                bar_char = self.BAR_CHARS['sonnet']
            else:
                bar_char = self.BAR_CHARS['opus']
            
            # タイムラインに配置
            for i in range(min(duration_blocks, width - start_pos)):
                if start_pos + i < width:
                    timeline[start_pos + i] = bar_char
        
        # 6時間ごとのマーカーを追加
        timeline_str = ''.join(timeline)
        marked_timeline = ''
        for i, char in enumerate(timeline_str):
            if i % 12 == 0:  # 6時間ごと
                marked_timeline += self.COLORS['GRAY'] + '|' + self.COLORS['ENDC']
            else:
                marked_timeline += char
        
        return marked_timeline

    def _get_cost_color(self, cost: float) -> str:
        """コストに応じた色を取得"""
        if cost >= 50:
            return self.COLORS['RED']
        elif cost >= 20:
            return self.COLORS['YELLOW']
        else:
            return self.COLORS['GREEN']

    def print_header(self):
        """ヘッダーを表示"""
        print(f"\n{self.COLORS['BOLD']}{self.COLORS['CYAN']}{'='*100}{self.COLORS['ENDC']}")
        print(f"{self.COLORS['BOLD']}{self.COLORS['HEADER']}Claude Code 使用実績タイムライン{self.COLORS['ENDC']}")
        
        if self.blocks:
            start_date = min(block.start_time.split(' ')[0] for block in self.blocks)
            end_date = max(block.start_time.split(' ')[0] for block in self.blocks)
            print(f"{self.COLORS['GRAY']}{start_date} - {end_date}{self.COLORS['ENDC']}")
        
        print(f"{self.COLORS['BOLD']}{self.COLORS['CYAN']}{'='*100}{self.COLORS['ENDC']}\n")

    def print_stats(self):
        """統計情報を表示"""
        if not self.blocks:
            print("データがありません")
            return
            
        total_duration = sum(d['total_duration'] for d in self.daily_data.values())
        total_cost = sum(d['total_cost'] for d in self.daily_data.values())
        total_tokens = sum(d['total_tokens'] for d in self.daily_data.values())
        total_entries = sum(d['total_entries'] for d in self.daily_data.values())
        total_blocks = len(self.blocks)
        
        print(f"{self.COLORS['BOLD']}統計情報:{self.COLORS['ENDC']}")
        print(f"  総使用時間: {self.COLORS['GREEN']}{total_duration//60}時間{total_duration%60}分{self.COLORS['ENDC']}")
        print(f"  総コスト: {self.COLORS['YELLOW']}${total_cost:.2f}{self.COLORS['ENDC']}")
        print(f"  総トークン数: {self.COLORS['CYAN']}{self._format_number(total_tokens)}{self.COLORS['ENDC']}")
        print(f"  総エントリー数: {self.COLORS['CYAN']}{total_entries}{self.COLORS['ENDC']}")
        print(f"  総ブロック数: {self.COLORS['CYAN']}{total_blocks}{self.COLORS['ENDC']}")
        print(f"  使用日数: {self.COLORS['CYAN']}{len(self.daily_data)}日{self.COLORS['ENDC']}")
        
        if total_blocks > 0:
            print(f"  平均ブロック時間: {self.COLORS['GREEN']}{(total_duration/total_blocks):.1f}分{self.COLORS['ENDC']}")
            print(f"  1日平均コスト: {self.COLORS['YELLOW']}${(total_cost/len(self.daily_data)):.2f}{self.COLORS['ENDC']}\n")

    def print_legend(self):
        """凡例を表示"""
        print(f"{self.COLORS['BOLD']}凡例:{self.COLORS['ENDC']}")
        print(f"  {self.BAR_CHARS['opus']} = Opus-4")
        print(f"  {self.BAR_CHARS['sonnet']} = Sonnet-4")
        print(f"  {self.BAR_CHARS['synthetic']} = Synthetic")
        print(f"  {self.BAR_CHARS['mixed']} = 複数モデル使用")
        print(f"  {self.BAR_CHARS['empty']} = 使用なし")
        print(f"  {self.COLORS['GRAY']}|{self.COLORS['ENDC']} = 6時間マーカー (0, 6, 12, 18時)")
        print()

    def print_timeline_table(self, filter_type: str = 'all', sort_by: str = None, limit: int = None):
        """タイムラインテーブルを表示"""
        if not self.daily_data:
            print("データがありません")
            return
            
        # ヘッダー
        print(f"{self.COLORS['BOLD']}日付        曜日  ブロック  時間     "
              f"タイムライン (00:00 ━━━━━━━━━━━━━━━━━━━━━━━━ 24:00)  "
              f"トークン数        コスト{self.COLORS['ENDC']}")
        print("─" * 100)
        
        # ソート処理
        if sort_by:
            dates_to_show = []
            if sort_by == 'cost':
                dates_to_show = sorted(self.daily_data.items(), 
                                     key=lambda x: x[1]['total_cost'], reverse=True)
            elif sort_by == 'duration':
                dates_to_show = sorted(self.daily_data.items(), 
                                     key=lambda x: x[1]['total_duration'], reverse=True)
            
            if limit:
                dates_to_show = dates_to_show[:limit]
                
            for date_str, data in dates_to_show:
                self._print_day_row(date_str, data, filter_type)
        else:
            # 日付順での表示
            sorted_dates = sorted(self.daily_data.keys())
            
            for date_str in sorted_dates:
                data = self.daily_data[date_str]
                
                # フィルタリング
                if filter_type == 'high-usage' and data['total_duration'] < 300:
                    continue
                if filter_type == 'high-cost' and data['total_cost'] < 50:
                    continue
                
                self._print_day_row(date_str, data, filter_type)
        
        print("─" * 100)

    def _print_day_row(self, date_str: str, data: Dict, filter_type: str = None):
        """1日分の行を表示"""
        # タイムラインバーを生成
        timeline_bar = self._get_timeline_bar(data['blocks'])
        
        # コストの色を取得
        cost_color = self._get_cost_color(data['total_cost'])
        
        # モデル情報
        models_str = ','.join(sorted(data['models']))
        if len(models_str) > 15:
            models_str = models_str[:12] + '...'
        
        # 表示
        print(f"{date_str}  ({self._get_weekday(date_str)})  "
              f"{len(data['blocks']):>2}ブロック  "
              f"{data['total_duration']//60:>2}h{data['total_duration']%60:>2}m  "
              f"{timeline_bar}  "
              f"{self._format_number(data['total_tokens']):>15}  "
              f"{cost_color}${data['total_cost']:>6.2f}{self.COLORS['ENDC']}")

    def print_daily_detail(self, date: str):
        """特定の日の詳細を表示"""
        if date not in self.daily_data:
            print(f"{self.COLORS['RED']}データがありません: {date}{self.COLORS['ENDC']}")
            return
            
        data = self.daily_data[date]
        self.print_header()
        
        print(f"{self.COLORS['BOLD']}{date} ({self._get_weekday(date)}) の詳細:{self.COLORS['ENDC']}")
        print("─" * 80)
        
        for block in data['blocks']:
            models_info = f"{self.COLORS['CYAN']}{','.join(block.models)}{self.COLORS['ENDC']}"
            print(f"  {block.start_time.split(' ')[1]:>5} - {block.duration_minutes//60:>2}h{block.duration_minutes%60:>2}m  "
                  f"{models_info:<30}  "
                  f"{self._format_number(block.total_tokens):>12} tokens  "
                  f"${block.cost_usd:>6.2f}  "
                  f"{self.COLORS['GRAY']}({block.entries} entries){self.COLORS['ENDC']}")
        
        print("─" * 80)
        print(f"  合計: {data['total_duration']//60}h{data['total_duration']%60}m  "
              f"{self._format_number(data['total_tokens']):>40} tokens  "
              f"{self._get_cost_color(data['total_cost'])}${data['total_cost']:>6.2f}{self.COLORS['ENDC']}\n")
        
        # タイムライン表示
        print(f"{self.COLORS['BOLD']}24時間タイムライン:{self.COLORS['ENDC']}")
        timeline_bar = self._get_timeline_bar(data['blocks'])
        print(f"  00:00 {timeline_bar} 24:00\n")

    def print_model_summary(self):
        """モデル別の使用状況を表示"""
        model_stats = {}
        
        for block in self.blocks:
            for model in block.models:
                if model not in model_stats:
                    model_stats[model] = {
                        'count': 0,
                        'duration': 0,
                        'tokens': 0,
                        'cost': 0
                    }
                
                model_stats[model]['count'] += 1
                model_stats[model]['duration'] += block.duration_minutes
                model_stats[model]['tokens'] += block.total_tokens
                model_stats[model]['cost'] += block.cost_usd
        
        print(f"\n{self.COLORS['BOLD']}モデル別使用状況:{self.COLORS['ENDC']}")
        print("─" * 60)
        
        for model, stats in sorted(model_stats.items(), key=lambda x: x[1]['cost'], reverse=True):
            print(f"{self.COLORS['CYAN']}{model:<15}{self.COLORS['ENDC']} "
                  f"使用回数: {stats['count']:>3}  "
                  f"時間: {stats['duration']//60:>3}h{stats['duration']%60:>2}m  "
                  f"コスト: {self.COLORS['YELLOW']}${stats['cost']:>7.2f}{self.COLORS['ENDC']}")
        
        print("─" * 60)

    def get_current_session_info(self):
        """現在のセッション情報を取得"""
        # Max $200プランの制限値（推測値）
        MAX_TOKENS_5H = 58679737  # 5時間の最大観測値から推測
        MAX_COST_5H = 127.27     # 5時間の最大観測値から推測
        
        # 現在時刻を取得
        now = datetime.datetime.now()
        
        # 現在の5時間ブロックを計算
        current_hour = now.hour
        block_start_hour = (current_hour // 5) * 5
        block_end_hour = block_start_hour + 5
        
        # リセット時刻を計算
        reset_time = now.replace(hour=block_end_hour % 24, minute=0, second=0, microsecond=0)
        if block_end_hour >= 24:
            reset_time += datetime.timedelta(days=1)
        
        # 現在のブロック内のセッションを取得
        current_block_sessions = []
        block_start_time = now.replace(hour=block_start_hour, minute=0, second=0, microsecond=0)
        
        for block in self.blocks:
            block_time = datetime.datetime.strptime(block.start_time, '%Y-%m-%d %H:%M')
            if block_time >= block_start_time and block_time < reset_time:
                current_block_sessions.append(block)
        
        # 統計を計算
        total_tokens = sum(b.total_tokens for b in current_block_sessions)
        total_cost = sum(b.cost_usd for b in current_block_sessions)
        
        # 主要モデルを取得
        model_counts = {}
        for block in current_block_sessions:
            for model in block.models:
                model_counts[model] = model_counts.get(model, 0) + 1
        
        primary_model = max(model_counts.items(), key=lambda x: x[1])[0] if model_counts else "N/A"
        
        # 使用率を計算
        usage_percent = (total_tokens / MAX_TOKENS_5H * 100) if MAX_TOKENS_5H > 0 else 0
        
        # 残り時間を計算
        time_remaining = reset_time - now
        hours_remaining = int(time_remaining.total_seconds() // 3600)
        minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)
        
        return {
            'model': primary_model,
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'max_tokens': MAX_TOKENS_5H,
            'usage_percent': usage_percent,
            'reset_time': reset_time.strftime('%H:%M'),
            'time_remaining': f"{hours_remaining}h{minutes_remaining}m",
            'session_count': len(current_block_sessions)
        }

    def print_current_session_line(self):
        """現在のセッション情報を1行で表示"""
        info = self.get_current_session_info()
        
        # 使用率に応じた色を決定
        if info['usage_percent'] >= 80:
            usage_color = self.COLORS['RED']
        elif info['usage_percent'] >= 50:
            usage_color = self.COLORS['YELLOW']
        else:
            usage_color = self.COLORS['GREEN']
        
        # 1行表示
        print(f"{self.COLORS['BOLD']}{info['model']:<10}{self.COLORS['ENDC']} "
              f"${info['total_cost']:>6.2f} "
              f"{self._format_number(info['total_tokens']):>12}/{self._format_number(info['max_tokens']):<12} "
              f"{usage_color}[{info['usage_percent']:>5.1f}%]{self.COLORS['ENDC']} "
              f"リセット: {self.COLORS['CYAN']}{info['reset_time']}{self.COLORS['ENDC']} "
              f"({info['time_remaining']}) "
              f"{self.COLORS['GRAY']}[{info['session_count']}セッション]{self.COLORS['ENDC']}")

def main():
    parser = argparse.ArgumentParser(
        description='Claude Code使用実績をターミナルで表示 (ccusage blocks --json対応)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  ccusage blocks --json | %(prog)s              # パイプで入力
  %(prog)s < blocks.json                        # ファイルから入力
  %(prog)s --file blocks.json                   # ファイル指定
  %(prog)s --high-usage                         # 高使用日のみ（5時間以上）
  %(prog)s --high-cost                          # 高コスト日のみ（$50以上）
  %(prog)s --sort-cost --limit 10               # コスト順で上位10日
  %(prog)s --date 2025-09-13                    # 特定日の詳細
  %(prog)s --model-summary                      # モデル別統計
"""
    )
    
    # 入力オプション
    parser.add_argument('--file', '-f', type=str,
                       help='JSONファイルのパス（指定しない場合は標準入力から読み込み）')
    
    # フィルタオプション
    filter_group = parser.add_mutually_exclusive_group()
    filter_group.add_argument('--high-usage', action='store_true',
                             help='高使用日のみ表示（5時間以上）')
    filter_group.add_argument('--high-cost', action='store_true',
                             help='高コスト日のみ表示（$50以上）')
    
    # ソートオプション
    sort_group = parser.add_mutually_exclusive_group()
    sort_group.add_argument('--sort-cost', action='store_true',
                           help='コスト順でソート')
    sort_group.add_argument('--sort-duration', action='store_true',
                           help='使用時間順でソート')
    
    # その他のオプション
    parser.add_argument('--date', type=str, metavar='YYYY-MM-DD',
                       help='特定の日の詳細を表示')
    parser.add_argument('--summary', action='store_true',
                       help='統計情報のみ表示')
    parser.add_argument('--model-summary', action='store_true',
                       help='モデル別の使用状況を表示')
    parser.add_argument('--no-color', action='store_true',
                       help='カラー表示を無効化')
    parser.add_argument('--no-legend', action='store_true',
                       help='凡例を表示しない')
    parser.add_argument('--limit', type=int, metavar='N',
                       help='表示する日数を制限（デフォルト: ソート時10日）')
    parser.add_argument('--current', action='store_true',
                       help='現在のセッション情報を1行で表示')
    
    args = parser.parse_args()
    
    # JSONデータの読み込み
    try:
        if args.file:
            with open(args.file, 'r') as f:
                json_data = json.load(f)
        else:
            # 標準入力から読み込み
            json_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"{parser.prog}: エラー: 有効なJSONデータではありません: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"{parser.prog}: エラー: ファイルが見つかりません: {args.file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"{parser.prog}: エラー: {e}", file=sys.stderr)
        sys.exit(1)
    
    # ビューアーの初期化とデータ読み込み
    viewer = ClaudeCodeViewer(no_color=args.no_color)
    viewer.load_from_json(json_data)
    
    # 現在のセッション情報を1行で表示
    if args.current:
        viewer.print_current_session_line()
        return
    
    # 特定日の詳細表示
    if args.date:
        viewer.print_daily_detail(args.date)
        return
    
    # モデル別統計のみ表示
    if args.model_summary:
        viewer.print_header()
        viewer.print_model_summary()
        return
    
    # 統計情報のみ表示
    if args.summary:
        viewer.print_header()
        viewer.print_stats()
        return
    
    # 通常の表示
    viewer.print_header()
    viewer.print_stats()
    
    if not args.no_legend:
        viewer.print_legend()
    
    # フィルタタイプの決定
    filter_type = 'all'
    if args.high_usage:
        filter_type = 'high-usage'
    elif args.high_cost:
        filter_type = 'high-cost'
    
    # ソートタイプの決定
    sort_by = None
    if args.sort_cost:
        sort_by = 'cost'
    elif args.sort_duration:
        sort_by = 'duration'
    
    # 表示制限
    limit = args.limit if args.limit else (10 if sort_by else None)
    
    # タイムライン表示
    viewer.print_timeline_table(filter_type=filter_type, sort_by=sort_by, limit=limit)

if __name__ == "__main__":
    main()