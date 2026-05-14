/**
 * Animasyonlu bot SVG illustration.
 * Hero section'da kullanılır — gözleri kırpışan, antenleri parlayan robot.
 */
export default function BotIllustration() {
  return (
    <div className="relative w-full max-w-md mx-auto">
      {/* Orbital rings */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-72 h-72 rounded-full border border-brand-500/20 animate-spin-slow" />
        <div className="absolute w-96 h-96 rounded-full border border-purple-500/10" style={{ animation: "spin-slow 30s linear infinite reverse" }} />
      </div>

      {/* Orbiting dots */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="absolute w-3 h-3 rounded-full bg-brand-400 animate-orbit shadow-lg shadow-brand-400/50" />
        <div className="absolute w-2 h-2 rounded-full bg-purple-400 animate-orbit-reverse shadow-lg shadow-purple-400/50" />
        <div className="absolute w-2 h-2 rounded-full bg-pink-400 animate-orbit shadow-lg shadow-pink-400/50" style={{ animationDelay: "-3s", animationDuration: "10s" }} />
      </div>

      {/* Bot SVG */}
      <svg
        viewBox="0 0 400 400"
        className="relative animate-float drop-shadow-[0_20px_50px_rgba(99,102,241,0.4)]"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="botBody" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="50%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#ec4899" />
          </linearGradient>
          <linearGradient id="botFace" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1e293b" />
            <stop offset="100%" stopColor="#0f172a" />
          </linearGradient>
          <radialGradient id="eyeGlow">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="100%" stopColor="#0891b2" />
          </radialGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Antenna */}
        <line x1="200" y1="80" x2="200" y2="40" stroke="url(#botBody)" strokeWidth="4" strokeLinecap="round" />
        <circle cx="200" cy="35" r="8" fill="#22d3ee" filter="url(#glow)">
          <animate attributeName="r" values="8;12;8" dur="2s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite" />
        </circle>

        {/* Head */}
        <rect x="120" y="80" width="160" height="140" rx="30" fill="url(#botBody)" />
        <rect x="135" y="95" width="130" height="110" rx="22" fill="url(#botFace)" />

        {/* Eyes */}
        <circle cx="170" cy="145" r="14" fill="url(#eyeGlow)" filter="url(#glow)">
          <animate attributeName="r" values="14;14;2;14;14" dur="4s" repeatCount="indefinite" keyTimes="0;0.45;0.5;0.55;1" />
        </circle>
        <circle cx="230" cy="145" r="14" fill="url(#eyeGlow)" filter="url(#glow)">
          <animate attributeName="r" values="14;14;2;14;14" dur="4s" repeatCount="indefinite" keyTimes="0;0.45;0.5;0.55;1" />
        </circle>

        {/* Mouth (smile) */}
        <path d="M 165 180 Q 200 200 235 180" stroke="#22d3ee" strokeWidth="3" strokeLinecap="round" fill="none" />

        {/* Side ears */}
        <circle cx="120" cy="150" r="10" fill="url(#botBody)" />
        <circle cx="280" cy="150" r="10" fill="url(#botBody)" />

        {/* Body */}
        <rect x="140" y="220" width="120" height="100" rx="20" fill="url(#botBody)" />
        <rect x="155" y="235" width="90" height="50" rx="8" fill="url(#botFace)" />

        {/* Chest screen lines */}
        <line x1="165" y1="250" x2="235" y2="250" stroke="#22d3ee" strokeWidth="2">
          <animate attributeName="x2" values="165;235;165" dur="3s" repeatCount="indefinite" />
        </line>
        <line x1="165" y1="260" x2="220" y2="260" stroke="#a78bfa" strokeWidth="2" opacity="0.7">
          <animate attributeName="x2" values="165;220;165" dur="3s" repeatCount="indefinite" begin="0.3s" />
        </line>
        <line x1="165" y1="270" x2="210" y2="270" stroke="#f472b6" strokeWidth="2" opacity="0.5">
          <animate attributeName="x2" values="165;210;165" dur="3s" repeatCount="indefinite" begin="0.6s" />
        </line>

        {/* Chest button */}
        <circle cx="200" cy="305" r="6" fill="#22d3ee">
          <animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite" />
        </circle>

        {/* Arms */}
        <rect x="100" y="230" width="40" height="20" rx="10" fill="url(#botBody)" />
        <rect x="260" y="230" width="40" height="20" rx="10" fill="url(#botBody)" />
        <circle cx="100" cy="240" r="14" fill="url(#botBody)" />
        <circle cx="300" cy="240" r="14" fill="url(#botBody)" />

        {/* Legs */}
        <rect x="160" y="320" width="25" height="40" rx="8" fill="url(#botBody)" />
        <rect x="215" y="320" width="25" height="40" rx="8" fill="url(#botBody)" />
        <rect x="155" y="355" width="35" height="12" rx="4" fill="#1e293b" />
        <rect x="210" y="355" width="35" height="12" rx="4" fill="#1e293b" />
      </svg>

      {/* Floating data icons */}
      <div className="absolute top-10 -left-4 glass rounded-lg px-3 py-2 text-xs text-brand-300 animate-float-slow border border-brand-500/30">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          <span className="font-mono">+247 ziyaret</span>
        </div>
      </div>

      <div className="absolute top-32 -right-4 glass rounded-lg px-3 py-2 text-xs text-purple-300 animate-float-slow border border-purple-500/30" style={{ animationDelay: "1s" }}>
        <div className="flex items-center gap-1.5">
          <span className="text-yellow-400">★</span>
          <span className="font-mono">3. sıra ↑</span>
        </div>
      </div>

      <div className="absolute bottom-20 -left-8 glass rounded-lg px-3 py-2 text-xs text-pink-300 animate-float-slow border border-pink-500/30" style={{ animationDelay: "2s" }}>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-pink-400 animate-pulse" />
          <span className="font-mono">42 proxy</span>
        </div>
      </div>
    </div>
  );
}
