"""
Scanner orchestration service.
Fetches bars → computes indicators → filters → scores → persists to DB.
"""
import asyncio
import logging
import uuid
from datetime import date, datetime, timezone
from time import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import ScanRun, ScanCandidate
from app.services.data_providers import get_market_provider, MarketDataProvider
from app.services.scanner.config import ScannerConfig, DEFAULT_CONFIG
from app.services.scanner.indicators import compute_indicators
from app.services.scanner.filters import apply_filters
from app.services.scanner.scorer import score_candidate

logger = logging.getLogger(__name__)

# Full S&P 500 universe
DEFAULT_UNIVERSE = [
    # Mega-cap Tech
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AVGO","ORCL",
    "ADBE","CRM","AMD","INTC","QCOM","TXN","AMAT","LRCX","KLAC","MRVL",
    "PANW","SNPS","CDNS","FTNT","ANSS","NFLX","UBER","ABNB","SHOP","SQ",
    "NOW","WDAY","TEAM","ZS","DDOG","MDB","SNOW","PLTR","COIN","RBLX",
    "NET","CRWD","OKTA","ZM","DOCU","TWLO","BILL","HUBS","VEEV","GTLB",
    # Financials
    "JPM","BAC","WFC","GS","MS","BLK","AXP","V","MA","COF",
    "SCHW","USB","PNC","TFC","FITB","C","BK","STT","DFS","RF",
    "HBAN","KEY","CFG","MTB","ZION","WBS","FHN","EWBC","PACW","WAL",
    "ICE","CME","SPGI","MCO","MSCI","FDS","BR","NTRS","IVZ","BEN",
    "MET","PRU","AFL","ALL","PGR","TRV","CB","AIG","HIG","LNC",
    # Healthcare
    "JNJ","UNH","LLY","ABBV","MRK","PFE","TMO","ABT","DHR","BMY",
    "AMGN","GILD","REGN","VRTX","ISRG","HCA","CI","CVS","ELV","HUM",
    "CNC","MOH","IQVIA","IQV","DGX","LH","BIO","HOLX","PODD","DXCM",
    "IDXX","MTD","WAT","A","ZBH","STE","BAX","BDX","BSX","EW",
    "MRNA","BNTX","BIIB","ALNY","INCY","EXAS","NTRA","NVAX","RARE","SRPT",
    # Consumer Discretionary
    "WMT","COST","TGT","HD","LOW","MCD","SBUX","NKE","CMG","YUM",
    "DG","DLTR","BKNG","MAR","HLT","LVS","MGM","WYNN","CZR","RCL",
    "CCL","NCLH","F","GM","RIVN","LCID","TM","HMC","RACE","MBLY",
    "ORLY","AZO","AAP","GPC","LKQ","AN","KMX","PAG","ABG","LAD",
    "AMZN","ETSY","EBAY","W","CHWY","CPRT","CVNA","VRM","KAR","IAA",
    # Consumer Staples
    "PG","KO","PEP","PM","MO","MDLZ","GIS","K","SJM","CAG",
    "CPB","HRL","MKC","CHD","CLX","CL","ENR","SPB","COTY","ELF",
    "WBA","RAD","WDFC","CENT","JJSF","LANC","CALM","SAFM","TSN","HRL",
    # Energy
    "XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","OXY","PXD",
    "DVN","FANG","MRO","APA","HAL","BKR","NOV","CTRA","SM","CPE",
    "WMB","KMI","OKE","EPD","ET","MPLX","PAA","TRGP","DT","LNG",
    # Industrials & Defense
    "GE","HON","CAT","DE","UNP","CSX","NSC","RTX","LMT","NOC",
    "BA","UPS","FDX","EMR","ETN","PH","ROK","GD","TDG","AXON",
    "MMM","ITW","DOV","XYL","CARR","OTIS","IR","TT","JCI","ALLE",
    "FAST","GWW","MSC","WSO","AIT","GATX","R","AL","WAB","TRN",
    "WM","RSG","CLH","CWST","US","JBHT","CHRW","ECHO","HUBG","XPO",
    # Communication & Media
    "DIS","CHTR","T","VZ","TMUS","FOXA","FOX","EA","TTWO","ATVI",
    "WBD","PARA","NWSA","IPG","OMC","PUB","MGNI","TTD","APPS","IS",
    # Materials
    "LIN","APD","ECL","NEM","FCX","NUE","VMC","MLM","PKG","IP",
    "CF","MOS","FMC","ALB","SQM","LTHM","ALTM","MP","LAC","PLL",
    "AA","CENX","HCC","ARCH","BTU","CEIX","SXC","AM","MPLX","TCP",
    # Utilities
    "NEE","DUK","SO","D","AEP","EXC","SRE","XEL","PEG","ED",
    "AWK","WEC","CMS","DTE","NI","OGE","POR","SWX","IDA","OTTR",
    # REITs
    "PLD","AMT","CCI","EQIX","PSA","O","SPG","WELL","AVB","EQR",
    "MAA","UDR","CPT","AIV","BRT","NHI","PEAK","VTR","SBAC","SBA",
    "GLPI","VICI","MGP","COLD","STAG","FR","EGP","TRNO","LPT","HIW",
]


async def _fetch_bars_batch(
    provider: MarketDataProvider,
    symbols: list[str],
    limit: int,
    batch_size: int = 10,
) -> dict[str, list]:
    """Fetch bars for all symbols in concurrent batches."""
    results: dict[str, list] = {}
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        tasks = [provider.get_bars(s, timeframe="1d", limit=limit) for s in batch]
        fetched = await asyncio.gather(*tasks, return_exceptions=True)
        for sym, data in zip(batch, fetched):
            if isinstance(data, Exception):
                logger.warning("Failed to fetch bars for %s: %s", sym, data)
            elif data:
                results[sym] = data
        await asyncio.sleep(0.3)  # polite delay between batches
    return results


async def run_scan(
    db: AsyncSession,
    config: ScannerConfig = DEFAULT_CONFIG,
    universe: list[str] = DEFAULT_UNIVERSE,
    mock_mode: bool = False,
    send_alert: bool = True,
) -> ScanRun:
    """
    Execute a full scan run. Creates and persists a ScanRun with candidates.
    Returns the completed ScanRun ORM object.
    """
    run_date = date.today()
    started_at = time()

    # Create scan run record
    scan_run = ScanRun(
        id=uuid.uuid4(),
        run_date=run_date,
        status="RUNNING",
        is_mocked=mock_mode,
    )
    db.add(scan_run)
    await db.flush()

    logger.info("Starting scan run %s for %d symbols", scan_run.id, len(universe))

    try:
        provider = get_market_provider()
        all_bars = await _fetch_bars_batch(provider, universe, limit=config.bars_needed)

        logger.info("Fetched bars for %d/%d symbols", len(all_bars), len(universe))

        candidates: list[ScanCandidate] = []
        tickers_scanned = 0

        for symbol in universe:
            bars = all_bars.get(symbol, [])
            if not bars:
                continue

            tickers_scanned += 1
            ind = compute_indicators(bars)
            if ind is None:
                logger.debug("Skipping %s — insufficient bars (%d)", symbol, len(bars))
                continue

            result = apply_filters(ind, config)
            if not result.passed:
                logger.debug("Filtered %s: %s", symbol, result.reason)
                continue

            breakdown = score_candidate(ind, config)
            if breakdown.total < config.min_final_score:
                logger.debug("Score too low %s: %.1f < %.1f", symbol, breakdown.total, config.min_final_score)
                continue

            candidate = ScanCandidate(
                id=uuid.uuid4(),
                scan_run_id=scan_run.id,
                run_date=run_date,
                symbol=symbol,
                score=breakdown.total,
                technical_score=breakdown.trend_score,
                sentiment_score=0.0,
                regime_modifier=0.0,
                confidence=breakdown.confidence,
                entry=round(ind.close, 2),
                stop=round(ind.close * 0.97, 2),
                target1=round(ind.close * 1.06, 2),
                rr_ratio=2.0,
                direction="LONG",
                strategy="swing_momentum",
                regime=None,
                technical_setup=(
                    f"Price above MA20 (${ind.ma20:.2f})"
                    + (f" and MA50 (${ind.ma50:.2f})" if ind.ma50 else "")
                    + f" · Rel vol {ind.relative_volume:.2f}x"
                    + (f" · Near {abs(ind.pct_from_high_20)*100:.1f}% from 20-day high" if ind.pct_from_high_20 < 0 else " · Above 20-day high")
                ),
                status="NEW",
            )
            candidates.append(candidate)

        # Sort by score descending, take top N
        candidates.sort(key=lambda c: c.score, reverse=True)
        candidates = candidates[: config.max_candidates]

        for c in candidates:
            db.add(c)

        scan_run.status = "COMPLETED"
        scan_run.tickers_scanned = tickers_scanned
        scan_run.candidates_found = len(candidates)
        scan_run.duration_ms = int((time() - started_at) * 1000)
        await db.flush()

        logger.info(
            "Scan %s complete: %d scanned, %d candidates in %dms",
            scan_run.id, tickers_scanned, len(candidates), scan_run.duration_ms,
        )

        # Fire alert (non-blocking)
        if send_alert:
            from app.core.config import settings as _settings
            if _settings.alert_email_enabled and _settings.alert_email_to:
                try:
                    from app.services.alerts.service import send_scan_summary
                    await send_scan_summary(scan_run.id, db)
                except Exception as alert_err:
                    logger.warning("Alert failed (scan still succeeded): %s", alert_err)

        return scan_run

    except Exception as e:
        scan_run.status = "FAILED"
        scan_run.error_message = str(e)
        await db.flush()
        logger.error("Scan %s failed: %s", scan_run.id, e)
        raise
