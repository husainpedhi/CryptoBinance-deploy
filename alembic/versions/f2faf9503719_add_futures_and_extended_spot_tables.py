"""add_futures_and_extended_spot_tables

Revision ID: f2faf9503719
Revises: 4bbd6cf5ad12
Create Date: 2026-05-09 17:11:18.418108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f2faf9503719'
down_revision: Union[str, None] = '4bbd6cf5ad12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('binance_agg_trades',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False),
    sa.Column('agg_trade_id', sa.BigInteger(), nullable=False),
    sa.Column('price', sa.Numeric(precision=30, scale=10), nullable=False),
    sa.Column('qty', sa.Numeric(precision=30, scale=10), nullable=False),
    sa.Column('first_trade_id', sa.BigInteger(), nullable=True),
    sa.Column('last_trade_id', sa.BigInteger(), nullable=True),
    sa.Column('trade_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_buyer_maker', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol', 'agg_trade_id', name='uq_binance_agg_trades_symbol_id')
    )
    op.create_index(op.f('ix_binance_agg_trades_agg_trade_id'), 'binance_agg_trades', ['agg_trade_id'], unique=False)
    op.create_index(op.f('ix_binance_agg_trades_symbol'), 'binance_agg_trades', ['symbol'], unique=False)
    op.create_index(op.f('ix_binance_agg_trades_trade_time'), 'binance_agg_trades', ['trade_time'], unique=False)

    op.create_table('binance_funding_rates',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False),
    sa.Column('funding_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('funding_rate', sa.Numeric(precision=20, scale=10), nullable=False),
    sa.Column('mark_price', sa.Numeric(precision=30, scale=10), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol', 'funding_time', name='uq_binance_funding_rates_symbol_time')
    )
    op.create_index(op.f('ix_binance_funding_rates_funding_time'), 'binance_funding_rates', ['funding_time'], unique=False)
    op.create_index(op.f('ix_binance_funding_rates_symbol'), 'binance_funding_rates', ['symbol'], unique=False)

    op.create_table('binance_futures_ohlcv',
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
    sa.UniqueConstraint('symbol', 'interval', 'open_time', name='uq_binance_futures_ohlcv_symbol_interval_open')
    )
    op.create_index(op.f('ix_binance_futures_ohlcv_open_time'), 'binance_futures_ohlcv', ['open_time'], unique=False)
    op.create_index(op.f('ix_binance_futures_ohlcv_symbol'), 'binance_futures_ohlcv', ['symbol'], unique=False)

    op.create_table('binance_liquidations',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False),
    sa.Column('side', sa.String(length=5), nullable=False),
    sa.Column('order_type', sa.String(length=20), nullable=True),
    sa.Column('time_in_force', sa.String(length=10), nullable=True),
    sa.Column('orig_qty', sa.Numeric(precision=30, scale=10), nullable=True),
    sa.Column('price', sa.Numeric(precision=30, scale=10), nullable=True),
    sa.Column('avg_price', sa.Numeric(precision=30, scale=10), nullable=True),
    sa.Column('order_status', sa.String(length=20), nullable=True),
    sa.Column('last_filled_qty', sa.Numeric(precision=30, scale=10), nullable=True),
    sa.Column('accumulated_qty', sa.Numeric(precision=30, scale=10), nullable=True),
    sa.Column('trade_time', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol', 'trade_time', 'price', 'orig_qty', name='uq_binance_liquidation_symbol_time_price_qty')
    )
    op.create_index(op.f('ix_binance_liquidations_symbol'), 'binance_liquidations', ['symbol'], unique=False)
    op.create_index(op.f('ix_binance_liquidations_trade_time'), 'binance_liquidations', ['trade_time'], unique=False)

    op.create_table('binance_long_short_ratio',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False),
    sa.Column('ratio_type', sa.String(length=20), nullable=False),
    sa.Column('period', sa.String(length=10), nullable=False),
    sa.Column('long_ratio', sa.Numeric(precision=10, scale=4), nullable=False),
    sa.Column('short_ratio', sa.Numeric(precision=10, scale=4), nullable=False),
    sa.Column('long_short_ratio', sa.Numeric(precision=10, scale=4), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol', 'ratio_type', 'period', 'timestamp', name='uq_binance_ls_ratio_symbol_type_period_ts')
    )
    op.create_index(op.f('ix_binance_long_short_ratio_symbol'), 'binance_long_short_ratio', ['symbol'], unique=False)
    op.create_index(op.f('ix_binance_long_short_ratio_timestamp'), 'binance_long_short_ratio', ['timestamp'], unique=False)

    op.create_table('binance_mark_price',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False),
    sa.Column('mark_price', sa.Numeric(precision=30, scale=10), nullable=False),
    sa.Column('index_price', sa.Numeric(precision=30, scale=10), nullable=True),
    sa.Column('estimated_settle_price', sa.Numeric(precision=30, scale=10), nullable=True),
    sa.Column('last_funding_rate', sa.Numeric(precision=20, scale=10), nullable=True),
    sa.Column('next_funding_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('interest_rate', sa.Numeric(precision=20, scale=10), nullable=True),
    sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binance_mark_price_fetched_at'), 'binance_mark_price', ['fetched_at'], unique=False)
    op.create_index(op.f('ix_binance_mark_price_symbol'), 'binance_mark_price', ['symbol'], unique=False)

    op.create_table('binance_open_interest',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False),
    sa.Column('open_interest', sa.Numeric(precision=30, scale=10), nullable=False),
    sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binance_open_interest_fetched_at'), 'binance_open_interest', ['fetched_at'], unique=False)
    op.create_index(op.f('ix_binance_open_interest_symbol'), 'binance_open_interest', ['symbol'], unique=False)

    op.create_table('binance_open_interest_hist',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False),
    sa.Column('period', sa.String(length=10), nullable=False),
    sa.Column('sum_open_interest', sa.Numeric(precision=30, scale=10), nullable=False),
    sa.Column('sum_open_interest_value', sa.Numeric(precision=30, scale=4), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol', 'period', 'timestamp', name='uq_binance_oi_hist_symbol_period_ts')
    )
    op.create_index(op.f('ix_binance_open_interest_hist_symbol'), 'binance_open_interest_hist', ['symbol'], unique=False)
    op.create_index(op.f('ix_binance_open_interest_hist_timestamp'), 'binance_open_interest_hist', ['timestamp'], unique=False)

    op.create_table('binance_order_book_depth',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False),
    sa.Column('side', sa.String(length=3), nullable=False),
    sa.Column('level', sa.Integer(), nullable=False),
    sa.Column('price', sa.Numeric(precision=30, scale=10), nullable=False),
    sa.Column('qty', sa.Numeric(precision=30, scale=10), nullable=False),
    sa.Column('last_update_id', sa.Integer(), nullable=True),
    sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binance_order_book_depth_fetched_at'), 'binance_order_book_depth', ['fetched_at'], unique=False)
    op.create_index(op.f('ix_binance_order_book_depth_symbol'), 'binance_order_book_depth', ['symbol'], unique=False)

    op.create_table('binance_taker_volume',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('symbol', sa.String(length=20), nullable=False),
    sa.Column('period', sa.String(length=10), nullable=False),
    sa.Column('buy_vol', sa.Numeric(precision=30, scale=10), nullable=False),
    sa.Column('sell_vol', sa.Numeric(precision=30, scale=10), nullable=False),
    sa.Column('buy_sell_ratio', sa.Numeric(precision=10, scale=4), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol', 'period', 'timestamp', name='uq_binance_taker_vol_symbol_period_ts')
    )
    op.create_index(op.f('ix_binance_taker_volume_symbol'), 'binance_taker_volume', ['symbol'], unique=False)
    op.create_index(op.f('ix_binance_taker_volume_timestamp'), 'binance_taker_volume', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_binance_taker_volume_timestamp'), table_name='binance_taker_volume')
    op.drop_index(op.f('ix_binance_taker_volume_symbol'), table_name='binance_taker_volume')
    op.drop_table('binance_taker_volume')
    op.drop_index(op.f('ix_binance_order_book_depth_symbol'), table_name='binance_order_book_depth')
    op.drop_index(op.f('ix_binance_order_book_depth_fetched_at'), table_name='binance_order_book_depth')
    op.drop_table('binance_order_book_depth')
    op.drop_index(op.f('ix_binance_open_interest_hist_timestamp'), table_name='binance_open_interest_hist')
    op.drop_index(op.f('ix_binance_open_interest_hist_symbol'), table_name='binance_open_interest_hist')
    op.drop_table('binance_open_interest_hist')
    op.drop_index(op.f('ix_binance_open_interest_symbol'), table_name='binance_open_interest')
    op.drop_index(op.f('ix_binance_open_interest_fetched_at'), table_name='binance_open_interest')
    op.drop_table('binance_open_interest')
    op.drop_index(op.f('ix_binance_mark_price_symbol'), table_name='binance_mark_price')
    op.drop_index(op.f('ix_binance_mark_price_fetched_at'), table_name='binance_mark_price')
    op.drop_table('binance_mark_price')
    op.drop_index(op.f('ix_binance_long_short_ratio_timestamp'), table_name='binance_long_short_ratio')
    op.drop_index(op.f('ix_binance_long_short_ratio_symbol'), table_name='binance_long_short_ratio')
    op.drop_table('binance_long_short_ratio')
    op.drop_index(op.f('ix_binance_liquidations_trade_time'), table_name='binance_liquidations')
    op.drop_index(op.f('ix_binance_liquidations_symbol'), table_name='binance_liquidations')
    op.drop_table('binance_liquidations')
    op.drop_index(op.f('ix_binance_futures_ohlcv_symbol'), table_name='binance_futures_ohlcv')
    op.drop_index(op.f('ix_binance_futures_ohlcv_open_time'), table_name='binance_futures_ohlcv')
    op.drop_table('binance_futures_ohlcv')
    op.drop_index(op.f('ix_binance_funding_rates_symbol'), table_name='binance_funding_rates')
    op.drop_index(op.f('ix_binance_funding_rates_funding_time'), table_name='binance_funding_rates')
    op.drop_table('binance_funding_rates')
    op.drop_index(op.f('ix_binance_agg_trades_trade_time'), table_name='binance_agg_trades')
    op.drop_index(op.f('ix_binance_agg_trades_symbol'), table_name='binance_agg_trades')
    op.drop_index(op.f('ix_binance_agg_trades_agg_trade_id'), table_name='binance_agg_trades')
    op.drop_table('binance_agg_trades')