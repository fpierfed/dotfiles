import time

from . import battery, cpu, datetime, memory, stock
from .stock import STOCK_SYMBOL


def status_text() -> str:
    # Seed the comparison values
    _ = cpu.status()
    _ = stock.status()

    c = cpu.status()
    cpu_pct = c['cpu_utilization_percent']

    m = memory.status()
    mem_free = m['memory_free_percent']

    parts = [
        f'CPU: {cpu_pct:.0f}%' if cpu_pct is not None else 'CPU: N/A',
        f'MEM: {mem_free}% free' if mem_free is not None else 'MEM: N/A',
    ]

    b = battery.status()
    bat_pct = b.get('charge_percent')
    bat_charging = b.get('is_charging')
    if bat_pct is not None:
        bat_text = f'{bat_pct:.0f}%'
        parts.append(
            'BAT: ' + (('⚡' + bat_text) if bat_charging else bat_text)
        )
    else:
        parts.append('BAT: N/A')

    s = stock.status()
    if s is not None and s[STOCK_SYMBOL]:
        parts.append(s[STOCK_SYMBOL])
    else:
        parts.append(f'{STOCK_SYMBOL}: N/A')

    t = datetime.status()
    parts.append(t['date'])
    parts.append(t['time'])
    return ' | '.join(parts) + ' '
