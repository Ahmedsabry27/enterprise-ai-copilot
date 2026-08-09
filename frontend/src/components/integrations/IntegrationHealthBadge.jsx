export default function IntegrationHealthBadge({health="unknown"}){return <span className={`integration-badge health-${health}`}>{health.replaceAll("_"," ")}</span>}
