#!/usr/bin/env python3
"""Calculate Levanta case metrics from raw amounts; never infer a missing BRB."""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import json
from pathlib import Path
import re


def decimal_value(value, field):
    if value is None or isinstance(value, bool):
        raise ValueError(f'{field} requires an explicit number')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f'{field} is not a number') from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f'{field} must be finite and nonnegative; review negative reports separately')
    return result


def calculate(document):
    if not isinstance(document, dict):
        raise ValueError('input must be a JSON object')
    currency = document.get('currency', '')
    if not isinstance(currency, str) or not re.fullmatch('[A-Z]{3}', currency):
        raise ValueError('currency requires an explicit three-letter code, e.g. USD')
    brands = document.get('brands')
    if not isinstance(brands, list) or not brands:
        raise ValueError('brands requires a nonempty list')
    prefix = '$' if currency == 'USD' else currency + ' '
    results = []
    for brand in brands:
        if not isinstance(brand, dict):
            raise ValueError('each brand must be a JSON object')
        label = brand.get('label')
        if not isinstance(label, str) or not label.strip():
            raise ValueError('Every brand requires a label')
        if brand.get('currency', currency) != currency:
            raise ValueError(f'{label}: mixed currencies must be separated')
        sales = decimal_value(brand.get('sales'), 'sales')
        commission = decimal_value(brand.get('commission'), 'commission')
        conversions = decimal_value(brand.get('conversions'), 'conversions')
        if conversions != conversions.to_integral_value():
            raise ValueError(f'{label}: conversions must be an integer')
        brb = None if brand.get('brb') is None else decimal_value(brand['brb'], 'brb')
        warnings = []
        with localcontext() as ctx:
            ctx.prec = 40
            net = None if brb is None else commission - brb
            aov = sales / conversions if conversions else None
            commission_rate = commission / sales if sales else None
            roas = sales / net if net is not None and net > 0 else None
            cost_rate = net / sales if net is not None and sales else None
            if brb is None:
                warnings.append('BRB is unknown; net cost, ROAS and analogous ACOS remain unknown.')
            if net is not None and net <= 0:
                warnings.append('Net commission cost is zero or negative; ROAS is not displayed. Review BRB and scope.')
            if sales == 0:
                warnings.append('Sales is zero; percentage metrics are undefined.')
            if conversions == 0:
                warnings.append('Conversions is zero; average order value is undefined.')
            raw = dict(sales=sales, conversions=conversions, commission=commission, brb=brb,
                       average_order_value=aov, commission_rate=commission_rate,
                       net_commission_cost=net, channel_roas=roas, net_commission_cost_rate=cost_rate)
            def money(value):
                return '—' if value is None else prefix + format(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP), ',.0f')
            def percent(value):
                return '—' if value is None else str((value * 100).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)) + '%'
            display = {
                'sales': money(sales), 'conversions': f'{int(conversions):,}',
                'average_order_value': money(aov), 'commission': money(commission),
                'commission_rate': percent(commission_rate), 'brb': money(brb),
                'net_commission_cost': money(net),
                'channel_roas': '—' if roas is None else str(roas.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)) + '×',
                'net_commission_cost_rate': percent(cost_rate),
            }
        results.append({'label': label, 'raw': {k: None if v is None else str(v) for k, v in raw.items()},
                        'display': display, 'warnings': warnings})
    return {'currency': currency, 'cost_scope': 'Commission minus actual/supplied BRB; excludes other fees', 'brands': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.input.read_text(encoding='utf-8'), parse_float=Decimal)
        result = calculate(document)
    except (ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
