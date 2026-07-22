import { useEffect, useState } from 'react'

export type MobileProfile = {
  isNarrow: boolean
  isCoarse: boolean
  reduceMotion: boolean
  isMobile: boolean
}

const query = () => {
  if (typeof window === 'undefined') {
    return { isNarrow: false, isCoarse: false, reduceMotion: false, isMobile: false }
  }
  const isNarrow = window.matchMedia('(max-width: 760px)').matches
  const isCoarse = window.matchMedia('(pointer: coarse)').matches
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  return {
    isNarrow,
    isCoarse,
    reduceMotion,
    isMobile: isNarrow || isCoarse,
  }
}

export function useMobileProfile(): MobileProfile {
  const [profile, setProfile] = useState<MobileProfile>(query)

  useEffect(() => {
    const narrow = window.matchMedia('(max-width: 760px)')
    const coarse = window.matchMedia('(pointer: coarse)')
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)')
    const sync = () => setProfile(query())
    narrow.addEventListener('change', sync)
    coarse.addEventListener('change', sync)
    motion.addEventListener('change', sync)
    sync()
    return () => {
      narrow.removeEventListener('change', sync)
      coarse.removeEventListener('change', sync)
      motion.removeEventListener('change', sync)
    }
  }, [])

  return profile
}
