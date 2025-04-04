// src/utils/timeUtils.js
import { DateTime } from 'luxon';

export const TimeAgo = (dateString) => {
  const date = DateTime.fromISO(dateString, { zone: 'utc' });
  const localDate = date.setZone(Intl.DateTimeFormat().resolvedOptions().timeZone);
  const now = DateTime.local();
  const seconds = Math.floor(now.diff(localDate, 'seconds').seconds);

  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

  const timeUnits = [
    { name: 'year', seconds: 60 * 60 * 24 * 365 },
    { name: 'month', seconds: 60 * 60 * 24 * 30 },
    { name: 'day', seconds: 60 * 60 * 24 },
    { name: 'hour', seconds: 60 * 60 },
    { name: 'minute', seconds: 60 },
    { name: 'second', seconds: 1 },
  ];

  for (const unit of timeUnits) {
    if (Math.abs(seconds) >= unit.seconds) {
      const timeValue = Math.round(seconds / unit.seconds);
      return rtf.format(timeValue, unit.name);
    }
  }
};
