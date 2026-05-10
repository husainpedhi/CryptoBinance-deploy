"""initial_schema

Revision ID: 4bbd6cf5ad12
Revises:
Create Date: 2026-05-09 15:16:41.416396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '4bbd6cf5ad12'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'binance_trading_pairs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('base_asset', sa.String(length=20), nullable=False),
        sa.Column('quote_asset', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('min_price', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('max_price', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('tick_size', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('min_qty', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('max_qty', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('step_size', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', name='uq_binance_trading_pairs_symbol'),
    )
    op.create_index(op.f('ix_binance_trading_pairs_symbol'), 'binance_trading_pairs', ['symbol'], unique=False)

    op.create_table(
        'binance_tickers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('price_change', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('price_change_percent', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('weighted_avg_price', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('prev_close_price', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('last_price', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('bid_price', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('ask_price', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('open_price', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('high_price', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('low_price', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('volume', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('quote_volume', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('open_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('close_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trade_count', sa.Integer(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_binance_tickers_symbol'), 'binance_tickers', ['symbol'], unique=False)
    op.create_index(op.f('ix_binance_tickers_fetched_at'), 'binance_tickers', ['fetched_at'], unique=False)

    op.create_table(
        'binance_ohlcv',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('interval', sa.String(length=10), nullable=False),
        sa.Column('open_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('close_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('open', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('high', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('low', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('close', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('volume', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('quote_asset_volume', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('trade_count', sa.Integer(), nullable=True),
        sa.Column('taker_buy_base_volume', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('taker_buy_quote_volume', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('kline_id', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'interval', 'open_time', name='uq_binance_ohlcv_symbol_interval_open'),
    )
    op.create_index(op.f('ix_binance_ohlcv_symbol'), 'binance_ohlcv', ['symbol'], unique=False)
    op.create_index(op.f('ix_binance_ohlcv_open_time'), 'binance_ohlcv', ['open_time'], unique=False)

    op.create_table(
        'binance_order_book',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('last_update_id', sa.Integer(), nullable=True),
        sa.Column('bid_price', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('bid_qty', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('ask_price', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('ask_qty', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('spread', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_binance_order_book_symbol'), 'binance_order_book', ['symbol'], unique=False)
    op.create_index(op.f('ix_binance_order_book_fetched_at'), 'binance_order_book', ['fetched_at'], unique=False)

    op.create_table(
        'binance_recent_trades',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('trade_id', sa.BigInteger(), nullable=False),
        sa.Column('price', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('qty', sa.Numeric(precision=30, scale=10), nullable=False),
        sa.Column('quote_qty', sa.Numeric(precision=30, scale=10), nullable=True),
        sa.Column('trade_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_buyer_maker', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'trade_id', name='uq_binance_recent_trades_symbol_trade'),
    )
    op.create_index(op.f('ix_binance_recent_trades_symbol'), 'binance_recent_trades', ['symbol'], unique=False)
    op.create_index(op.f('ix_binance_recent_trades_trade_id'), 'binance_recent_trades', ['trade_id'], unique=False)
    op.create_index(op.f('ix_binance_recent_trades_trade_time'), 'binance_recent_trades', ['trade_time'], unique=False)

    op.create_table(
        'binance_scheduler_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('records_processed', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_binance_scheduler_logs_job_name'), 'binance_scheduler_logs', ['job_name'], unique=False)
    op.create_index(op.f('ix_binance_scheduler_logs_started_at'), 'binance_scheduler_logs', ['started_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_binance_scheduler_logs_started_at'), table_name='binance_scheduler_logs')
    op.drop_index(op.f('ix_binance_scheduler_logs_job_name'), table_name='binance_scheduler_logs')
    op.drop_table('binance_scheduler_logs')
    op.drop_index(op.f('ix_binance_recent_trades_trade_time'), table_name='binance_recent_trades')
    op.drop_index(op.f('ix_binance_recent_trades_trade_id'), table_name='binance_recent_trades')
    op.drop_index(op.f('ix_binance_recent_trades_symbol'), table_name='binance_recent_trades')
    op.drop_table('binance_recent_trades')
    op.drop_index(op.f('ix_binance_order_book_fetched_at'), table_name='binance_order_book')
    op.drop_index(op.f('ix_binance_order_book_symbol'), table_name='binance_order_book')
    op.drop_table('binance_order_book')
    op.drop_index(op.f('ix_binance_ohlcv_open_time'), table_name='binance_ohlcv')
    op.drop_index(op.f('ix_binance_ohlcv_symbol'), table_name='binance_ohlcv')
    op.drop_table('binance_ohlcv')
    op.drop_index(op.f('ix_binance_tickers_fetched_at'), table_name='binance_tickers')
    op.drop_index(op.f('ix_binance_tickers_symbol'), table_name='binance_tickers')
    op.drop_table('binance_tickers')
    op.drop_index(op.f('ix_binance_trading_pairs_symbol'), table_name='binance_trading_pairs')
    op.drop_table('binance_trading_pairs')