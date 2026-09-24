"use client";

import { useState } from "react";

type TraceItem = {
  step: number;
  type: string;
  tool?: string;
  content?: string;
  result?: Record<string, unknown>;
};

type AgentResponse = {
  goal: string;
  status: string;
  trace: TraceItem[];
  steps: number;
};

type Approval = {
  id: string;
  status: string;
  tool: string;
  arguments: Record<string, unknown>;
  result?: Record<string, unknown>;
};

type HealthState = {
  status: string;
  service?: string;
  version?: string;
};

const API_URL = "http://localhost:8000";

export default function Home() {
  const [goal, setGoal] = useState(
    "Investigate the current application incident and determine the likely cause and appropriate remediation."
  );

  const [agentResult, setAgentResult] = useState<AgentResponse | null>(null);
  const [approval, setApproval] = useState<Approval | null>(null);
  const [deployment, setDeployment] = useState<HealthState | null>(null);
  const [health, setHealth] = useState<HealthState | null>(null);

  const [loading, setLoading] = useState(false);
  const [approvalLoading, setApprovalLoading] = useState(false);
  const [approvalLoadingState, setApprovalLoadingState] = useState(false);
  const [recoveryLoading, setRecoveryLoading] = useState(false);

  const [error, setError] = useState("");

  async function runAgent() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/agent/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ goal }),
      });

      if (!response.ok) {
        const body = await response.text();

        throw new Error(
          body || `Agent request failed with status ${response.status}.`
        );
      }

      const data: AgentResponse = await response.json();

      setAgentResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while contacting OpsPilot."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadApprovals() {
    setApprovalLoadingState(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/approvals`);

      if (!response.ok) {
        throw new Error("Could not load approval requests.");
      }

      const data = await response.json();

      const pendingApproval = data.approvals.find(
        (item: Approval) =>
          item.status === "pending" &&
          item.tool === "rollback_deployment"
      );

      if (pendingApproval) {
        setApproval(pendingApproval);
      } else {
        setApproval(null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load approval requests."
      );
    } finally {
      setApprovalLoadingState(false);
    }
  }

  async function createApproval() {
    setApprovalLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/approvals`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tool: "rollback_deployment",
          arguments: {},
        }),
      });

      if (!response.ok) {
        const body = await response.text();

        throw new Error(
          body || "Could not create approval request."
        );
      }

      const data: Approval = await response.json();

      setApproval(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not create approval request."
      );
    } finally {
      setApprovalLoading(false);
    }
  }

  async function approveRollback() {
    if (!approval) {
      return;
    }

    setApprovalLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/approvals/${approval.id}/approve`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const body = await response.text();

        throw new Error(
          body || `Approval failed with status ${response.status}.`
        );
      }

      const data: Approval = await response.json();

      setApproval(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Rollback approval failed."
      );
    } finally {
      setApprovalLoading(false);
    }
  }

  async function verifyRecovery() {
    setRecoveryLoading(true);
    setError("");

    try {
      const [deploymentResponse, healthResponse] = await Promise.all([
        fetch(
          `${API_URL}/api/agent/tools/get_deployment_status/execute`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({}),
          }
        ),
        fetch(
          `${API_URL}/api/agent/tools/get_application_health/execute`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({}),
          }
        ),
      ]);

      if (!deploymentResponse.ok || !healthResponse.ok) {
        throw new Error("Recovery verification failed.");
      }

      const deploymentData = await deploymentResponse.json();
      const healthData = await healthResponse.json();

      setDeployment(deploymentData);
      setHealth(healthData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Recovery verification failed."
      );
    } finally {
      setRecoveryLoading(false);
    }
  }

  function getTraceIcon(type: string) {
    if (type === "goal") return "🎯";
    if (type === "tool_call") return "🔧";
    if (type === "observation") return "🔍";
    if (type === "final_answer") return "🤖";

    return "•";
  }

  const rollbackApproved = approval?.status === "approved";

  const recoveryVerified =
    deployment?.status === "healthy" &&
    health?.status === "healthy";

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/90">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/15 text-xl">
              ⚡
            </div>

            <div>
              <h1 className="text-xl font-bold tracking-tight">
                OpsPilot
              </h1>

              <p className="text-xs text-slate-400">
                Agentic DevOps Operations
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-sm text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Agent Online
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-8">
        {/* System status */}
        <section className="mb-8 grid gap-4 md:grid-cols-3">
          <StatusCard
            title="API"
            value="Healthy"
            detail="FastAPI service"
          />

          <StatusCard
            title="Database"
            value="Connected"
            detail="PostgreSQL"
          />

          <StatusCard
            title="Agent"
            value="Ready"
            detail="LLM + tool calling"
          />
        </section>

        {/* Main panels */}
        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          {/* Investigation panel */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
            <div className="mb-6 flex items-start justify-between">
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-cyan-400">
                  Incident investigation
                </p>

                <h2 className="text-2xl font-bold">
                  Autonomous DevOps Investigation
                </h2>

                <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400">
                  OpsPilot investigates application health, logs, and
                  deployment state before recommending remediation.
                </p>
              </div>

              <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs font-medium text-red-400">
                INCIDENT
              </div>
            </div>

            <label className="mb-2 block text-sm font-medium text-slate-300">
              Agent goal
            </label>

            <textarea
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
              rows={5}
              className="w-full resize-none rounded-xl border border-slate-700 bg-slate-950 p-4 text-sm text-slate-200 outline-none transition focus:border-cyan-500"
            />

            <button
              onClick={runAgent}
              disabled={loading || !goal.trim()}
              className="mt-4 w-full rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Agent Investigating..." : "Run OpsPilot Agent"}
            </button>

            <button
              onClick={loadApprovals}
              disabled={approvalLoadingState}
              className="mt-3 w-full rounded-xl border border-slate-700 bg-slate-950 px-5 py-3 font-semibold text-slate-300 transition hover:border-cyan-500 hover:text-cyan-300 disabled:opacity-50"
            >
              {approvalLoadingState
                ? "Loading Approvals..."
                : "Load Pending Approvals"}
            </button>

            {error && (
              <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
                {error}
              </div>
            )}
          </div>

          {/* Environment panel */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
            <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-cyan-400">
              Current environment
            </p>

            <h2 className="text-xl font-bold">Development</h2>

            <div className="mt-6 space-y-4">
              <InfoRow
                label="Service"
                value="opspilot-api"
              />

              <InfoRow
                label="Deployment"
                value={rollbackApproved ? "1.0.0" : "1.0.1"}
                valueClass={
                  rollbackApproved
                    ? "text-emerald-400"
                    : "text-red-400"
                }
              />

              <InfoRow
                label="Health"
                value={recoveryVerified ? "Healthy" : "Unhealthy"}
                valueClass={
                  recoveryVerified
                    ? "text-emerald-400"
                    : "text-red-400"
                }
              />

              <InfoRow
                label="Error rate"
                value={recoveryVerified ? "Normal" : "High"}
                valueClass={
                  recoveryVerified
                    ? "text-emerald-400"
                    : "text-red-400"
                }
              />

              <InfoRow
                label="Incident"
                value={
                  recoveryVerified
                    ? "Resolved"
                    : "Database connectivity"
                }
                valueClass={
                  recoveryVerified
                    ? "text-emerald-400"
                    : "text-amber-400"
                }
              />
            </div>

            {!approval && (
              <div className="mt-6 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                <p className="text-sm font-semibold text-amber-300">
                  No approval loaded
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Load the pending approval from the OpsPilot backend.
                </p>

                <button
                  onClick={createApproval}
                  disabled={approvalLoading}
                  className="mt-4 w-full rounded-lg bg-amber-400 px-4 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-amber-300 disabled:opacity-50"
                >
                  {approvalLoading
                    ? "Creating Approval..."
                    : "Create Rollback Approval"}
                </button>
              </div>
            )}

            {approval && !rollbackApproved && (
              <div className="mt-6 rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
                <p className="text-sm font-semibold text-amber-300">
                  ⚠ Human approval required
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Action: rollback deployment
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Approval ID: {approval.id}
                </p>

                <button
                  onClick={approveRollback}
                  disabled={approvalLoading}
                  className="mt-4 w-full rounded-lg bg-amber-400 px-4 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-amber-300 disabled:opacity-50"
                >
                  {approvalLoading
                    ? "Approving Rollback..."
                    : "Approve Rollback"}
                </button>
              </div>
            )}

            {rollbackApproved && !recoveryVerified && (
              <div className="mt-6 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4">
                <p className="text-sm font-semibold text-emerald-300">
                  ✓ Rollback completed
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Deployment was rolled back from 1.0.1 to 1.0.0.
                </p>

                <button
                  onClick={verifyRecovery}
                  disabled={recoveryLoading}
                  className="mt-4 w-full rounded-lg bg-emerald-400 px-4 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-emerald-300 disabled:opacity-50"
                >
                  {recoveryLoading
                    ? "Verifying Recovery..."
                    : "Verify Recovery"}
                </button>
              </div>
            )}

            {recoveryVerified && (
              <div className="mt-6 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
                <p className="text-sm font-semibold text-emerald-300">
                  ✓ Recovery verified
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Deployment and application health are both healthy.
                </p>
              </div>
            )}
          </div>
        </section>

        {/* Agent trace */}
        <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400">
                Agent execution
              </p>

              <h2 className="mt-1 text-xl font-bold">
                Investigation Trace
              </h2>
            </div>

            {agentResult && (
              <div className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-400">
                {agentResult.steps} agent steps
              </div>
            )}
          </div>

          {!agentResult ? (
            <div className="rounded-xl border border-dashed border-slate-700 p-8 text-center">
              <div className="text-3xl">🤖</div>

              <p className="mt-3 font-medium text-slate-300">
                No investigation running
              </p>

              <p className="mt-1 text-sm text-slate-500">
                Run the agent to see its tool calls, observations,
                and final assessment.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {agentResult.trace.map((item, index) => (
                <div
                  key={`${item.step}-${index}`}
                  className="flex gap-4 rounded-xl border border-slate-800 bg-slate-950/70 p-4"
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-800">
                    {getTraceIcon(item.type)}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-semibold text-slate-500">
                        STEP {item.step}
                      </span>

                      <span className="text-xs uppercase tracking-wider text-cyan-400">
                        {item.type.replace("_", " ")}
                      </span>
                    </div>

                    {item.tool && (
                      <p className="mt-1 font-mono text-sm text-slate-200">
                        {item.tool}
                      </p>
                    )}

                    {item.content && (
                      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-400">
                        {item.content}
                      </p>
                    )}

                    {item.result && (
                      <pre className="mt-2 overflow-x-auto rounded-lg bg-black/30 p-3 text-xs leading-5 text-slate-400">
                        {JSON.stringify(item.result, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Recovery evidence */}
        {recoveryVerified && (
          <section className="mt-6 grid gap-6 md:grid-cols-2">
            <EvidenceCard
              title="Deployment verification"
              icon="🚀"
              value={deployment?.version ?? "1.0.0"}
              detail="Healthy deployment"
            />

            <EvidenceCard
              title="Application verification"
              icon="❤️"
              value="Healthy"
              detail="Health check passed"
            />
          </section>
        )}

        {/* DevOps Improvement Report */}
        <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400">
                Continuous improvement
              </p>

              <h2 className="mt-1 text-xl font-bold">
                DevOps Improvement Report
              </h2>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                OpsPilot converts incident evidence into actionable
                improvements for the software delivery and operations
                process.
              </p>
            </div>

            <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-xs font-medium text-cyan-300">
              POST-INCIDENT
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            {/* Findings */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5">
              <h3 className="font-semibold text-slate-200">
                Incident findings
              </h3>

              <ul className="mt-4 space-y-3 text-sm text-slate-400">
                <li className="flex gap-3">
                  <span className="text-red-400">●</span>
                  Database connection failures were detected.
                </li>

                <li className="flex gap-3">
                  <span className="text-red-400">●</span>
                  Database connection timeouts caused request failures.
                </li>

                <li className="flex gap-3">
                  <span className="text-red-400">●</span>
                  HTTP 500 responses and failed health checks occurred.
                </li>

                <li className="flex gap-3">
                  <span className="text-amber-400">●</span>
                  The failure was associated with deployment 1.0.1.
                </li>

                <li className="flex gap-3">
                  <span className="text-emerald-400">●</span>
                  Rollback to 1.0.0 restored application health.
                </li>
              </ul>
            </div>

            {/* Recommendations */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-5">
              <h3 className="font-semibold text-slate-200">
                Recommended improvements
              </h3>

              <div className="mt-4 space-y-3">
                <ImprovementItem
                  number="01"
                  title="Validate database configuration in CI"
                  detail="Check required database settings before deployment."
                />

                <ImprovementItem
                  number="02"
                  title="Add database connectivity tests"
                  detail="Verify application-to-database connectivity before release."
                />

                <ImprovementItem
                  number="03"
                  title="Add post-deployment health checks"
                  detail="Verify service health before considering a deployment successful."
                />

                <ImprovementItem
                  number="04"
                  title="Define rollback thresholds"
                  detail="Use measurable health and error-rate conditions to trigger remediation workflows."
                />

                <ImprovementItem
                  number="05"
                  title="Block unhealthy releases"
                  detail="Prevent failed health verification from being treated as a successful deployment."
                />
              </div>
            </div>
          </div>

          <div className="mt-6 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
            <div className="flex items-center gap-3">
              <span className="text-xl">📈</span>

              <div>
                <p className="text-sm font-semibold text-cyan-300">
                  DevOps focus
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Improve deployment reliability by moving validation
                  earlier in the delivery pipeline and verifying system
                  health after deployment.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Architecture */}
        <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400">
            Agent architecture
          </p>

          <div className="mt-5 grid gap-3 text-center text-sm md:grid-cols-5">
            <ArchitectureStep label="User Goal" icon="🎯" />
            <ArchitectureStep label="AI Agent" icon="🤖" />
            <ArchitectureStep label="Tool Registry" icon="🔧" />
            <ArchitectureStep label="DevOps System" icon="⚙️" />
            <ArchitectureStep label="Verified Result" icon="✅" />
          </div>
        </section>
      </div>
    </main>
  );
}

function StatusCard({
  title,
  value,
  detail,
}: {
  title: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">{title}</span>

        <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
      </div>

      <p className="mt-3 text-xl font-bold">{value}</p>

      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </div>
  );
}

function InfoRow({
  label,
  value,
  valueClass = "text-slate-200",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
      <span className="text-sm text-slate-500">{label}</span>

      <span className={`text-sm font-medium ${valueClass}`}>
        {value}
      </span>
    </div>
  );
}

function EvidenceCard({
  title,
  icon,
  value,
  detail,
}: {
  title: string;
  icon: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5">
      <div className="flex items-center gap-3">
        <span className="text-xl">{icon}</span>

        <div>
          <p className="text-sm font-semibold text-emerald-300">
            {title}
          </p>

          <p className="mt-1 text-xs text-slate-500">
            {detail}
          </p>
        </div>
      </div>

      <p className="mt-4 text-2xl font-bold text-white">
        {value}
      </p>
    </div>
  );
}

function ImprovementItem({
  number,
  title,
  detail,
}: {
  number: string;
  title: string;
  detail: string;
}) {
  return (
    <div className="flex gap-3 rounded-lg border border-slate-800 p-3">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-cyan-500/10 text-xs font-bold text-cyan-400">
        {number}
      </div>

      <div>
        <p className="text-sm font-medium text-slate-200">
          {title}
        </p>

        <p className="mt-1 text-xs leading-5 text-slate-500">
          {detail}
        </p>
      </div>
    </div>
  );
}

function ArchitectureStep({
  label,
  icon,
}: {
  label: string;
  icon: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
      <div className="text-xl">{icon}</div>

      <p className="mt-2 text-xs font-medium text-slate-300">
        {label}
      </p>
    </div>
  );
}