export const projectLinks = {
  github: 'https://github.com/Mbjaradat/LapSim-AI',
  // Set VITE_RESEARCH_INTEREST_URL at build time. No enrollment/data collection.
  researchInterest: import.meta.env.VITE_RESEARCH_INTEREST_URL ?? 'https://forms.gle/Jz6Wva2JEVHcomc36',
};
export function externalResearchUrl(value:string):string|null {
  if(!value.trim())return null;
  try{const url=new URL(value);return url.protocol==='https:'&&!url.username&&!url.password?url.href:null;}catch{return null;}
}
