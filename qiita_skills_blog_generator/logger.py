"""
ロガー

実行ログの記録を担当します。
要件10.1〜10.6に対応。
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """
    実行ログの記録を管理するクラス
    
    処理の開始/終了、スキル処理状況、エラー、警告を記録します。
    要件10: 実行ログの記録
    """
    
    def __init__(self, log_level: str, log_file: Path):
        """
        Loggerを初期化する
        
        Args:
            log_level: ログレベル（DEBUG、INFO、WARNING、ERROR、CRITICAL）
            log_file: ログファイルのパス
        """
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
        
        # ログレベルを設定（要件10.6）
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # 既存のハンドラをクリア（重複を防ぐ）
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
        
        # ログファイルのディレクトリを作成
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # ファイルハンドラを設定
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        
        # コンソールハンドラを設定
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        
        # フォーマッタを設定
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # ハンドラを追加
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.start_time: Optional[datetime] = None
    
    def log_start(self) -> None:
        """
        処理開始をログに記録する
        
        要件10.1: 処理開始時刻をログに記録する
        """
        self.start_time = datetime.now()
        self.logger.info("=" * 60)
        self.logger.info("Qiita技術ブログ生成システム - 処理開始")
        self.logger.info(f"開始時刻: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)
    
    def log_skill_processed(self, skill_name: str, status: str) -> None:
        """
        スキル処理状況をログに記録する
        
        Args:
            skill_name: スキル名
            status: 処理状況（success、skip、error）
            
        要件10.2: 各スキルの処理状況（成功/スキップ/エラー）をログに記録する
        """
        status_messages = {
            'success': f"✓ スキル処理成功: {skill_name}",
            'skip': f"⊘ スキルをスキップ: {skill_name}",
            'error': f"✗ スキル処理エラー: {skill_name}"
        }
        
        message = status_messages.get(status, f"スキル処理: {skill_name} - {status}")
        
        if status == 'success':
            self.logger.info(message)
        elif status == 'skip':
            self.logger.warning(message)
        elif status == 'error':
            self.logger.error(message)
        else:
            self.logger.info(message)
    
    def log_error(self, message: str, exception: Optional[Exception] = None, 
                  file_path: Optional[str] = None, cause: Optional[str] = None,
                  solution: Optional[str] = None) -> None:
        """
        エラーをログに記録する
        
        エラーメッセージには以下を含める：
        - 何が起きたか（事象）
        - どこで起きたか（場所）
        - なぜ起きたか（原因）
        - どうすればよいか（対処方法）
        
        Args:
            message: エラーメッセージ（事象）
            exception: 例外オブジェクト（オプション）
            file_path: エラーが発生したファイルパス（場所）
            cause: エラーの原因
            solution: 対処方法
            
        要件10.4: エラーの詳細情報をログに記録する
        """
        error_parts = [f"ERROR: {message}"]
        
        if file_path:
            error_parts.append(f"場所: {file_path}")
        
        if cause:
            error_parts.append(f"原因: {cause}")
        elif exception:
            error_parts.append(f"原因: {type(exception).__name__}: {str(exception)}")
        
        if solution:
            error_parts.append(f"対処: {solution}")
        
        full_message = "\n".join(error_parts)
        self.logger.error(full_message)
        
        # 例外のスタックトレースをデバッグレベルで記録
        if exception:
            self.logger.debug("スタックトレース:", exc_info=exception)
    
    def log_warning(self, message: str, file_path: Optional[str] = None,
                   cause: Optional[str] = None, solution: Optional[str] = None) -> None:
        """
        警告をログに記録する
        
        Args:
            message: 警告メッセージ
            file_path: 警告が発生したファイルパス（オプション）
            cause: 警告の原因（オプション）
            solution: 対処方法（オプション）
            
        要件10.4: 警告の詳細情報をログに記録する
        """
        warning_parts = [f"WARNING: {message}"]
        
        if file_path:
            warning_parts.append(f"場所: {file_path}")
        
        if cause:
            warning_parts.append(f"原因: {cause}")
        
        if solution:
            warning_parts.append(f"対処: {solution}")
        
        full_message = "\n".join(warning_parts)
        self.logger.warning(full_message)
    
    def log_end(self, success_count: int, skip_count: int, error_count: int = 0) -> None:
        """
        処理終了をログに記録する
        
        Args:
            success_count: 成功したスキル数
            skip_count: スキップしたスキル数
            error_count: エラーが発生したスキル数（デフォルト: 0）
            
        要件10.1: 処理終了時刻をログに記録する
        """
        end_time = datetime.now()
        
        if self.start_time:
            duration = end_time - self.start_time
            duration_str = str(duration).split('.')[0]  # マイクロ秒を除去
        else:
            duration_str = "不明"
        
        self.logger.info("=" * 60)
        self.logger.info("処理完了")
        self.logger.info(f"終了時刻: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"処理時間: {duration_str}")
        self.logger.info(f"成功: {success_count}件")
        self.logger.info(f"スキップ: {skip_count}件")
        if error_count > 0:
            self.logger.info(f"エラー: {error_count}件")
        self.logger.info(f"合計: {success_count + skip_count + error_count}件")
        self.logger.info("=" * 60)
    
    def log_output_file(self, file_path: Path) -> None:
        """
        生成された記事のファイルパスをログに記録する
        
        Args:
            file_path: 出力ファイルのパス
            
        要件10.3: 生成された記事のファイルパスをログに記録する
        """
        self.logger.info(f"記事を出力しました: {file_path}")
    
    def log_config(self, config_dict: dict) -> None:
        """
        使用した設定内容をログに記録する
        
        Args:
            config_dict: 設定の辞書表現
            
        要件9.4: 使用した設定内容をログに記録する
        """
        self.logger.info("使用する設定:")
        for key, value in config_dict.items():
            self.logger.info(f"  {key}: {value}")
    
    def debug(self, message: str) -> None:
        """デバッグメッセージを記録"""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """情報メッセージを記録"""
        self.logger.info(message)
    
    def close(self) -> None:
        """
        ロガーのリソースをクリーンアップする
        
        すべてのハンドラを閉じてリソースを解放します。
        """
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
