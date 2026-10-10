import assert from 'node:assert/strict';
import test from 'node:test';
import { averageUptime, formatUptimePercent } from '../uptime.js';

test('no data is shown as no data, not a perfect record', () => {
    assert.equal(formatUptimePercent(undefined), '—');
    assert.equal(formatUptimePercent(null), '—');
    assert.equal(averageUptime([]), null);
    assert.equal(averageUptime([{}, { uptime_30d: null }]), null);
});

test('a fully down component counts as 0%, not 100%', () => {
    assert.equal(formatUptimePercent(0), '0.00%');
    assert.equal(averageUptime([{ uptime_30d: 0 }, { uptime_30d: 100 }]), 50);
});

test('components without a figure do not pull the average', () => {
    assert.equal(averageUptime([{ uptime_30d: 99.5 }, {}]), 99.5);
    assert.equal(formatUptimePercent(averageUptime([{ uptime_30d: 99.5 }, {}])), '99.50%');
});
