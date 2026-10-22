/** Deterministic animation helpers driven by the caller's timeline. */
function finite(...values) {
  if (values.some(value => !Number.isFinite(value))) {
    throw new RangeError('Motion values must be finite numbers');
  }
}

export function clamp(value, lower = 0, upper = 1) {
  finite(value, lower, upper);
  if (upper < lower) throw new RangeError('Bounds must be ordered');
  if (value < lower) return lower;
  if (value > upper) return upper;
  return value;
}

export function progress(time, start, end) {
  finite(time, start, end);
  if (end <= start) throw new RangeError('Motion interval must increase');
  return clamp((time - start) / (end - start));
}

/** Quadratic ease-in/ease-out with exact endpoints and midpoint. */
export function smooth(value) {
  const position = clamp(value);
  if (position <= 0.5) return 2 * position ** 2;
  return 1 - 2 * (1 - position) ** 2;
}

export function at(time, start, end) {
  return smooth(progress(time, start, end));
}

/** Cubic arrival plus a small polynomial overshoot, settling exactly at 1. */
export function settle(time, start, duration = 0.8) {
  finite(duration);
  if (duration <= 0) throw new RangeError('Duration must be positive');
  const position = progress(time, start, start + duration);
  const remaining = 1 - position;
  return 1 - remaining ** 3 + 1.2 * position * remaining ** 2;
}

export function vis(time, start, end, fade = 0.2) {
  finite(time, start, end, fade);
  if (end <= start || fade <= 0) throw new RangeError('Invalid visibility interval');
  if (time <= start || time >= end) return 0;
  const ramp = Math.min(fade, (end - start) / 2);
  const distanceFromEdge = Math.min(time - start, end - time);
  return smooth(distanceFromEdge / ramp);
}

export function lerp(start, end, position) {
  finite(start, end);
  const weight = clamp(position);
  return (1 - weight) * start + weight * end;
}

/** de Casteljau evaluation of a cubic curve in two dimensions. */
export function bezier(start, control1, control2, end, position) {
  let points = [start, control1, control2, end].map(point => {
    if (!Array.isArray(point) || point.length !== 2) throw new RangeError('Expected an XY point');
    finite(...point);
    return point.slice();
  });
  const weight = clamp(position);
  while (points.length > 1) {
    points = points.slice(1).map((point, index) =>
      point.map((coordinate, axis) => lerp(points[index][axis], coordinate, weight)));
  }
  return points[0];
}

export function strokeValues(length, position) {
  finite(length);
  if (length < 0) throw new RangeError('Path length must be nonnegative');
  const visibleLength = length * clamp(position);
  return {strokeDasharray: length, strokeDashoffset: length - visibleLength};
}

export function stroke(path, position) {
  const attributes = strokeValues(path.getTotalLength(), position);
  for (const [property, value] of Object.entries(attributes)) path.style[property] = String(value);
  return attributes;
}

export const MOTION = Object.freeze({smooth, at, settle, vis, bezier, stroke});
