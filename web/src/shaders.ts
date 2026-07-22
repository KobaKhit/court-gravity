export const courtVertexShader = /* glsl */ `
uniform vec3 uPlayers[16];
uniform float uSigma[16];
uniform int uCount;
uniform float uZScale;
uniform int uMode; // 0=net, 1=offense, 2=defense
uniform int uKernel; // 0=gaussian, 1=softened
uniform float uSoftening;
varying float vH;
varying vec2 vUv;
varying vec2 vCourt;
varying vec3 vWorldPos;
varying float vOffenseH;
varying float vDefenseH;

float influence(vec2 p, vec3 pl, float s) {
  vec2 d = p - pl.xy;
  float m = abs(pl.z);
  if (uKernel == 1) {
    return m / sqrt(dot(d,d) + uSoftening * uSoftening);
  }
  return m * exp(-dot(d,d) / (2.0 * s * s));
}

void main() {
  vUv = uv;
  vec3 p = position;
  vCourt = p.xy + vec2(0.0, 47.0);
  float offenseH = 0.0;
  float defenseH = 0.0;
  for (int i = 0; i < 16; i++) {
    if (i >= uCount) break;
    float signedMass = uPlayers[i].z;
    bool isOff = signedMass < 0.0;
    float I = influence(vCourt, uPlayers[i], uSigma[i]);
    if (isOff) offenseH += I;
    else defenseH += I;
  }
  float h = uMode == 1 ? -offenseH : (uMode == 2 ? defenseH : defenseH - offenseH);
  vH = h;
  vOffenseH = uMode == 2 ? 0.0 : offenseH;
  vDefenseH = uMode == 1 ? 0.0 : defenseH;
  // Keep extreme slider values from crossing the arena foundation.
  p.z = clamp(h * uZScale, -5.5, 5.5);
  vec4 world = modelMatrix * vec4(p, 1.0);
  vWorldPos = world.xyz;
  gl_Position = projectionMatrix * viewMatrix * world;
}
`

export const courtFragmentShader = /* glsl */ `
varying float vH;
varying vec2 vUv;
varying vec2 vCourt;
varying vec3 vWorldPos;
varying float vOffenseH;
varying float vDefenseH;
uniform float uColorScale;

float lineMask(float d, float width) {
  return 1.0 - smoothstep(width, width + 0.18, abs(d));
}

float rectangleLine(vec2 p, vec2 halfSize, float width) {
  vec2 q = abs(p) - halfSize;
  float outside = length(max(q, 0.0));
  float inside = min(max(q.x, q.y), 0.0);
  return lineMask(outside + inside, width);
}

float courtMarkings(vec2 p) {
  float lines = 0.0;
  // Full 94 × 50 ft court border.
  lines = max(lines, rectangleLine(p - vec2(0.0, 47.0), vec2(24.75, 46.75), 0.12));
  // Paint / lanes at both baskets.
  lines = max(lines, rectangleLine(p - vec2(0.0, 9.5), vec2(8.0, 9.5), 0.12));
  lines = max(lines, rectangleLine(p - vec2(0.0, 84.5), vec2(8.0, 9.5), 0.12));
  // Free throw circles.
  lines = max(lines, lineMask(abs(length(p - vec2(0.0, 19.0)) - 6.0), 0.12));
  lines = max(lines, lineMask(abs(length(p - vec2(0.0, 75.0)) - 6.0), 0.12));
  // Restricted areas.
  float restrictedNear = lineMask(abs(length(p - vec2(0.0, 4.0)) - 4.0), 0.11) * step(4.0, p.y);
  float restrictedFar = lineMask(abs(length(p - vec2(0.0, 90.0)) - 4.0), 0.11) * step(p.y, 90.0);
  lines = max(lines, max(restrictedNear, restrictedFar));
  // Three-point arcs meet the 22-foot corner lines at their exact geometric
  // intersection: sqrt(23.75² - 22²) = 8.947 feet from each basket.
  float cornerBreakNear = 12.947;
  float cornerBreakFar = 81.053;
  float arcNear = lineMask(abs(length(p - vec2(0.0, 4.0)) - 23.75), 0.13)
    * smoothstep(cornerBreakNear - 0.15, cornerBreakNear + 0.15, p.y);
  float arcFar = lineMask(abs(length(p - vec2(0.0, 90.0)) - 23.75), 0.13)
    * (1.0 - smoothstep(cornerBreakFar - 0.15, cornerBreakFar + 0.15, p.y));
  float cornersNear = max(lineMask(abs(p.x) - 22.0, 0.11), 0.0)
    * (1.0 - smoothstep(cornerBreakNear - 0.15, cornerBreakNear + 0.15, p.y));
  float cornersFar = max(lineMask(abs(p.x) - 22.0, 0.11), 0.0)
    * smoothstep(cornerBreakFar - 0.15, cornerBreakFar + 0.15, p.y);
  float nearThree = min(1.0, arcNear + cornersNear);
  float farThree = min(1.0, arcFar + cornersFar);
  lines = max(lines, max(nearThree, farThree));
  // Mid-court line and center circle.
  lines = max(lines, lineMask(p.y - 47.0, 0.12));
  lines = max(lines, lineMask(abs(length(p - vec2(0.0, 47.0)) - 6.0), 0.12));
  return clamp(lines, 0.0, 1.0);
}

void main() {
  // Reconstruct the displaced normal for convincing moving highlights.
  vec3 dpdx = dFdx(vWorldPos);
  vec3 dpdy = dFdy(vWorldPos);
  vec3 normal = normalize(cross(dpdx, dpdy));
  if (normal.z < 0.0) normal *= -1.0;
  vec3 lightDir = normalize(vec3(-0.35, -0.25, 0.9));
  float diffuse = 0.45 + 0.55 * max(dot(normal, lightDir), 0.0);
  float rim = pow(1.0 - max(normal.z, 0.0), 2.0);

  // Polished maple floor with alternating plank bands and subtle grain.
  float plank = mod(floor((vCourt.x + 25.0) / 2.1), 2.0);
  float grain = sin(vCourt.y * 1.7 + sin(vCourt.x * 0.43) * 2.2) * 0.025;
  vec3 mapleA = vec3(0.30, 0.205, 0.115);
  vec3 mapleB = vec3(0.38, 0.265, 0.145);
  vec3 hardwood = mix(mapleA, mapleB, plank * 0.34 + 0.32 + grain);

  // Weather-map palette: broad blue opportunity systems and softer coral
  // defensive pressure, with stepped intensity bands like radar products.
  vec3 wellDeep = vec3(0.01, 0.22, 0.62);
  vec3 wellBright = vec3(0.18, 0.88, 1.00);
  vec3 peak = vec3(0.96, 0.13, 0.055);
  float scale = max(uColorScale, 0.001);
  float rawOffense = smoothstep(0.018, 0.82, vOffenseH / scale);
  float rawDefense = smoothstep(0.018, 0.82, vDefenseH / scale);
  // The executive view communicates advantage, not two opaque layers.
  // Equal local influence cancels to neutral; separation exposes blue while
  // tighter defensive control exposes red.
  float netAdvantage = (vOffenseH - vDefenseH) / scale;
  float offenseStrength = smoothstep(0.015, 0.64, max(netAdvantage, 0.0));
  float defenseStrength = smoothstep(0.015, 0.64, max(-netAdvantage, 0.0));
  float contested = min(rawOffense, rawDefense) * (1.0 - max(offenseStrength, defenseStrength));
  // Keep the fills temporally continuous; isobars provide the weather-map
  // structure without discrete color bands popping between frames.
  float weatherOffense = offenseStrength;
  float weatherDefense = defenseStrength;
  vec3 well = mix(wellDeep, wellBright, smoothstep(0.18, 0.92, offenseStrength));
  float fieldStrength = max(offenseStrength, defenseStrength);
  vec3 fieldColor = offenseStrength >= defenseStrength ? well : peak;
  vec3 neutralPressure = vec3(0.43, 0.46, 0.49);
  vec3 color = mix(hardwood, neutralPressure, contested * 0.18);
  color = mix(color, well, weatherOffense * 0.70);
  color = mix(color, peak, weatherDefense * 0.54);
  color += peak * defenseStrength * 0.04;

  // Independent isobars reveal overlapping systems even where net height
  // cancels out, matching a weather-pressure visualization.
  float offenseWave = abs(fract(vOffenseH * 4.6 + 0.5) - 0.5);
  float defenseWave = abs(fract(vDefenseH * 4.2 + 0.5) - 0.5);
  float offenseIsobar = (1.0 - smoothstep(0.455, 0.5, offenseWave)) * offenseStrength;
  float defenseIsobar = (1.0 - smoothstep(0.455, 0.5, defenseWave)) * defenseStrength;
  color += wellBright * offenseIsobar * 0.22;
  color += peak * defenseIsobar * 0.075;
  float defensePulse = (1.0 - smoothstep(0.43, 0.5, abs(fract(vDefenseH * 4.0) - 0.5))) * defenseStrength;
  color += peak * defensePulse * 0.08;

  float lines = courtMarkings(vCourt);
  color = mix(color, vec3(0.92, 0.94, 0.96), lines * 0.92);
  color *= diffuse;
  color += fieldColor * (fieldStrength * 0.16 + rim * 0.12);

  // Baseline vignette keeps the center luminous and cinematic.
  float edge = smoothstep(0.72, 1.0, max(abs(vUv.x - 0.5), abs(vUv.y - 0.5)) * 2.0);
  color *= 1.0 - edge * 0.22;
  gl_FragColor = vec4(color, 1.0);
}
`
