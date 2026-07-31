import { Bot, CheckCircle, Workflow, Zap } from "lucide-react";
import AgentStatus from "../../components/dashboard/AgentStatus";
import DashboardHeader from "../../components/dashboard/DashboardHeader";
import DashboardError from "../../components/dashboard/DashboardError";
import DashboardSkeleton from "../../components/dashboard/DashboardSkeleton";
import ExecutionOverviewChart from "../../components/dashboard/ExecutionOverviewChart";
import MetricCard from "../../components/dashboard/MetricCard";
import RecentExecutions from "../../components/dashboard/RecentExecutions";
import WorkflowDistribution from "../../components/dashboard/WorkflowDistribution";
import { useDashboard } from "../../hooks/useDashboard";

export default function DashboardPage(){const dashboard=useDashboard(); if(dashboard.isLoading)return <DashboardSkeleton/>; if(dashboard.error)return <DashboardError onRetry={dashboard.refetch}/>; const {metrics,trends,recent,agents,distribution}=dashboard; const cards=[['Total Workflows',metrics.total_workflows,metrics.trends.workflows,Workflow],['Active Agents',metrics.active_agents,metrics.trends.agents,Bot],['Actions Executed',metrics.actions_executed,metrics.trends.actions,Zap],['Success Rate',`${metrics.success_rate}%`,metrics.trends.success,CheckCircle]]; return <main className="min-h-full bg-gradient-to-br from-[#071426] via-[#0B1F3A] to-[#142B52] p-5 text-white md:p-8"><DashboardHeader/><div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([title,value,trend,icon])=><MetricCard key={title} title={title} value={value} trend={trend} icon={icon}/>)}</div><div className="mt-6 grid gap-6 xl:grid-cols-2"><ExecutionOverviewChart data={trends}/><RecentExecutions items={recent}/><AgentStatus agents={agents}/><WorkflowDistribution distribution={distribution}/></div></main>}
