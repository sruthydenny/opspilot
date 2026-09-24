"use client";

import {
  FormEvent,
  useSyncExternalStore,
  useState,
} from "react";

const API_URL = "http://localhost:8000";

const STORAGE_KEYS = {
  token: "opspilot_token",
  user: "opspilot_user",
  projects: "opspilot_projects",
  selectedProject: "opspilot_selected_project",
};

type User = {
  id: number;
  email: string;
};

type Project = {
  id: number;
  name: string;
  repository_url?: string | null;
  application_url?: string | null;
  health_endpoint?: string | null;
  environment: string;
  deployment_status: string;
  current_version: string;
};

type Approval = {
  id: number;
  status: string;
  tool: string;
  arguments: Record<string, unknown>;
  result?: Record<string, unknown>;
};

type AgentResponse = {
  goal: string;
  status: string;
  trace: Array<Record<string, unknown>>;
  steps: number;
  approval_required?: {
    approval_id?: string;
    tool?: string;
    status?: string;
    arguments?: Record<string, unknown>;
  };
};

function getStorageSnapshot(key: string): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(key) ?? "";
}

function subscribeToStorage(
  key: string,
  callback: () => void
): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }

  const eventName = `opspilot-storage-${key}`;

  const handler = () => {
    callback();
  };

  window.addEventListener("storage", handler);
  window.addEventListener(eventName, handler);

  return () => {
    window.removeEventListener("storage", handler);
    window.removeEventListener(eventName, handler);
  };
}

function useStoredValue(key: string): string {
  return useSyncExternalStore(
    (callback) => subscribeToStorage(key, callback),
    () => getStorageSnapshot(key),
    () => ""
  );
}

function writeStorage(key: string, value: string): void {
  localStorage.setItem(key, value);

  window.dispatchEvent(
    new Event(`opspilot-storage-${key}`)
  );
}

function removeStorage(key: string): void {
  localStorage.removeItem(key);

  window.dispatchEvent(
    new Event(`opspilot-storage-${key}`)
  );
}

function parseStoredValue<T>(
  value: string,
  fallback: T
): T {
  if (!value) {
    return fallback;
  }

  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}

export default function Home() {
  const token = useStoredValue(STORAGE_KEYS.token);

  const userRaw = useStoredValue(STORAGE_KEYS.user);
  const projectsRaw = useStoredValue(STORAGE_KEYS.projects);
  const selectedProjectRaw = useStoredValue(
    STORAGE_KEYS.selectedProject
  );

  const user = parseStoredValue<User | null>(
    userRaw,
    null
  );

  const projects = parseStoredValue<Project[]>(
    projectsRaw,
    []
  );

  const selectedProjectId = selectedProjectRaw
    ? Number(selectedProjectRaw)
    : null;

  const selectedProject =
    projects.find(
      (project) => project.id === selectedProjectId
    ) ?? null;

  const [authMode, setAuthMode] = useState<
    "login" | "register"
  >("login");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [projectName, setProjectName] = useState("");
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [applicationUrl, setApplicationUrl] = useState("");
  const [healthEndpoint, setHealthEndpoint] = useState("");
  const [environment, setEnvironment] =
    useState("production");

  const [goal, setGoal] = useState(
    "Investigate the current application incident and determine the likely cause and appropriate remediation."
  );

  const [agentResult, setAgentResult] =
    useState<AgentResponse | null>(null);

  const [approvals, setApprovals] = useState<
    Approval[]
  >([]);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function loadProjects(
    authToken: string,
    selectFirst = false
  ) {
    try {
      const response = await fetch(
        `${API_URL}/api/projects`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to load projects."
        );
      }

      const nextProjects: Project[] = data.projects ?? [];

      writeStorage(
        STORAGE_KEYS.projects,
        JSON.stringify(nextProjects)
      );

      if (selectFirst && nextProjects.length > 0) {
        writeStorage(
          STORAGE_KEYS.selectedProject,
          String(nextProjects[0].id)
        );
      }
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to load projects."
      );
    }
  }

  async function handleAuth(event: FormEvent) {
    event.preventDefault();

    setLoading(true);
    setMessage("");

    try {
      const endpoint =
        authMode === "login"
          ? "/api/auth/login"
          : "/api/auth/register";

      const response = await fetch(
        `${API_URL}${endpoint}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Authentication failed."
        );
      }

      writeStorage(
        STORAGE_KEYS.token,
        data.token
      );

      writeStorage(
        STORAGE_KEYS.user,
        JSON.stringify(data.user)
      );

      setEmail("");
      setPassword("");
      setMessage("");

      await loadProjects(data.token, true);
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Authentication failed."
      );
    } finally {
      setLoading(false);
    }
  }

  async function createProject(event: FormEvent) {
    event.preventDefault();

    if (!token) {
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/api/projects`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: projectName,
            repository_url:
              repositoryUrl || null,
            application_url:
              applicationUrl || null,
            health_endpoint:
              healthEndpoint || null,
            environment,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to create project."
        );
      }

      setProjectName("");
      setRepositoryUrl("");
      setApplicationUrl("");
      setHealthEndpoint("");

      writeStorage(
        STORAGE_KEYS.selectedProject,
        String(data.id)
      );

      await loadProjects(token);

      setMessage(
        "Project created successfully."
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to create project."
      );
    } finally {
      setLoading(false);
    }
  }

  async function simulateIncident() {
    if (!selectedProject || !token) {
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/api/projects/${selectedProject.id}/simulate-incident`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to simulate incident."
        );
      }

      await loadProjects(token);

      setMessage(
        "Incident simulated for the selected project."
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to simulate incident."
      );
    } finally {
      setLoading(false);
    }
  }

  async function runAgent() {
    if (!selectedProject || !token) {
      return;
    }

    setLoading(true);
    setMessage("");
    setAgentResult(null);

    try {
      const response = await fetch(
        `${API_URL}/api/projects/${selectedProject.id}/agent/run`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            goal,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            "Agent request failed."
        );
      }

      setAgentResult(data);

      if (data.approval_required) {
        setMessage(
          "OpsPilot recommends an action requiring approval."
        );

        await loadApprovals(
          selectedProject.id
        );
      } else {
        setMessage(
          "OpsPilot completed the investigation."
        );
      }
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Agent request failed."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadApprovals(projectId: number) {
    if (!token) {
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/api/projects/${projectId}/approvals`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to load approvals."
        );
      }

      setApprovals(data.approvals ?? []);
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to load approvals."
      );
    }
  }

  async function createRollbackApproval() {
    if (!selectedProject || !token) {
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/api/projects/${selectedProject.id}/approvals`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            tool: "rollback_deployment",
            arguments: {},
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to create approval."
        );
      }

      await loadApprovals(
        selectedProject.id
      );

      setMessage(
        `Approval request #${data.id} created.`
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to create approval."
      );
    } finally {
      setLoading(false);
    }
  }

  async function approveRollback(
    approvalId: number
  ) {
    if (!selectedProject || !token) {
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/api/projects/${selectedProject.id}/approvals/${approvalId}/approve`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to approve action."
        );
      }

      await loadApprovals(
        selectedProject.id
      );

      await loadProjects(token);

      setMessage(
        "Rollback approved and executed."
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to approve action."
      );
    } finally {
      setLoading(false);
    }
  }

  function selectProject(projectId: number) {
    writeStorage(
      STORAGE_KEYS.selectedProject,
      String(projectId)
    );

    setAgentResult(null);

    void loadApprovals(projectId);
  }

  function logout() {
    removeStorage(STORAGE_KEYS.token);
    removeStorage(STORAGE_KEYS.user);
    removeStorage(STORAGE_KEYS.projects);
    removeStorage(STORAGE_KEYS.selectedProject);

    setAgentResult(null);
    setApprovals([]);
    setMessage("");
  }

  if (!token || !user) {
    return (
      <main className="min-h-screen bg-slate-950 text-white">
        <div className="mx-auto flex min-h-screen max-w-md items-center px-6">
          <div className="w-full rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
            <div className="mb-8">
              <p className="text-sm font-medium text-cyan-400">
                Agentic DevOps Platform
              </p>

              <h1 className="mt-2 text-3xl font-bold">
                OpsPilot
              </h1>

              <p className="mt-2 text-sm text-slate-400">
                Connect your projects and let OpsPilot
                investigate operational problems.
              </p>
            </div>

            <div className="mb-6 flex rounded-lg bg-slate-800 p-1">
              <button
                className={`flex-1 rounded-md px-4 py-2 text-sm ${
                  authMode === "login"
                    ? "bg-cyan-500 text-slate-950"
                    : "text-slate-400"
                }`}
                onClick={() =>
                  setAuthMode("login")
                }
              >
                Login
              </button>

              <button
                className={`flex-1 rounded-md px-4 py-2 text-sm ${
                  authMode === "register"
                    ? "bg-cyan-500 text-slate-950"
                    : "text-slate-400"
                }`}
                onClick={() =>
                  setAuthMode("register")
                }
              >
                Register
              </button>
            </div>

            <form
              onSubmit={handleAuth}
              className="space-y-4"
            >
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-400"
              />

              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                required
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-400"
              />

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-lg bg-cyan-500 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50"
              >
                {loading
                  ? "Please wait..."
                  : authMode === "login"
                    ? "Login"
                    : "Create Account"}
              </button>
            </form>

            {message && (
              <p className="mt-4 rounded-lg bg-slate-800 p-3 text-sm text-slate-300">
                {message}
              </p>
            )}
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <header className="flex flex-col gap-4 border-b border-slate-800 pb-6 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-cyan-400">
              Agentic DevOps Platform
            </p>

            <h1 className="text-3xl font-bold">
              OpsPilot
            </h1>

            <p className="mt-1 text-sm text-slate-400">
              Supervise AI-powered incident investigation
              and controlled remediation.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-400">
              {user.email}
            </span>

            <button
              onClick={logout}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-slate-500"
            >
              Logout
            </button>
          </div>
        </header>

        {message && (
          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300">
            {message}
          </div>
        )}

        <section className="mt-6 grid gap-6 lg:grid-cols-[320px_1fr]">
          <aside className="space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">
                  My Projects
                </h2>

                <button
                  onClick={() =>
                    void loadProjects(token)
                  }
                  className="text-xs text-cyan-400"
                >
                  Refresh
                </button>
              </div>

              <div className="mt-4 space-y-2">
                {projects.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No projects yet.
                  </p>
                ) : (
                  projects.map((project) => (
                    <button
                      key={project.id}
                      onClick={() =>
                        selectProject(project.id)
                      }
                      className={`w-full rounded-xl border px-4 py-3 text-left ${
                        selectedProject?.id ===
                        project.id
                          ? "border-cyan-400 bg-cyan-500/10"
                          : "border-slate-800 bg-slate-950"
                      }`}
                    >
                      <p className="font-medium">
                        {project.name}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        {project.environment}
                      </p>

                      <p className="mt-2 text-xs text-slate-400">
                        {project.deployment_status}
                      </p>
                    </button>
                  ))
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <h2 className="font-semibold">
                Add Project
              </h2>

              <form
                onSubmit={createProject}
                className="mt-4 space-y-3"
              >
                <input
                  placeholder="Project name"
                  value={projectName}
                  onChange={(event) =>
                    setProjectName(
                      event.target.value
                    )
                  }
                  required
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                />

                <input
                  placeholder="GitHub repository URL"
                  value={repositoryUrl}
                  onChange={(event) =>
                    setRepositoryUrl(
                      event.target.value
                    )
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                />

                <input
                  placeholder="Application URL"
                  value={applicationUrl}
                  onChange={(event) =>
                    setApplicationUrl(
                      event.target.value
                    )
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                />

                <input
                  placeholder="Health endpoint"
                  value={healthEndpoint}
                  onChange={(event) =>
                    setHealthEndpoint(
                      event.target.value
                    )
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                />

                <select
                  value={environment}
                  onChange={(event) =>
                    setEnvironment(
                      event.target.value
                    )
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                >
                  <option value="development">
                    Development
                  </option>

                  <option value="staging">
                    Staging
                  </option>

                  <option value="production">
                    Production
                  </option>
                </select>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-50"
                >
                  Create Project
                </button>
              </form>
            </div>
          </aside>

          <section className="space-y-6">
            {!selectedProject ? (
              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8">
                <h2 className="text-xl font-semibold">
                  Select a project
                </h2>

                <p className="mt-2 text-sm text-slate-400">
                  Create or select a project before
                  using OpsPilot.
                </p>
              </div>
            ) : (
              <>
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-cyan-400">
                        Selected Project
                      </p>

                      <h2 className="mt-1 text-2xl font-bold">
                        {selectedProject.name}
                      </h2>

                      <p className="mt-2 text-sm text-slate-400">
                        Environment:{" "}
                        {selectedProject.environment}
                      </p>

                      <p className="text-sm text-slate-400">
                        Deployment:{" "}
                        {selectedProject.deployment_status}
                      </p>

                      <p className="text-sm text-slate-400">
                        Version:{" "}
                        {selectedProject.current_version}
                      </p>
                    </div>

                    <button
                      onClick={simulateIncident}
                      disabled={loading}
                      className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm text-amber-300 disabled:opacity-50"
                    >
                      Simulate Incident
                    </button>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold">
                        Ask OpsPilot
                      </h2>

                      <p className="mt-1 text-sm text-slate-400">
                        OpsPilot is operating on the
                        selected project.
                      </p>
                    </div>

                    <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs text-cyan-400">
                      Project #{selectedProject.id}
                    </span>
                  </div>

                  <textarea
                    value={goal}
                    onChange={(event) =>
                      setGoal(event.target.value)
                    }
                    rows={4}
                    className="mt-5 w-full rounded-xl border border-slate-700 bg-slate-950 p-4 text-sm outline-none focus:border-cyan-400"
                  />

                  <button
                    onClick={runAgent}
                    disabled={loading}
                    className="mt-4 rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"
                  >
                    {loading
                      ? "OpsPilot is working..."
                      : "Run OpsPilot Agent"}
                  </button>
                </div>

                {agentResult && (
                  <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                    <h2 className="text-lg font-semibold">
                      Investigation Trace
                    </h2>

                    <div className="mt-4 space-y-3">
                      {agentResult.trace.map(
                        (entry, index) => (
                          <div
                            key={index}
                            className="rounded-xl border border-slate-800 bg-slate-950 p-4"
                          >
                            <p className="text-xs uppercase tracking-wide text-slate-500">
                              {String(entry.type)}
                            </p>

                            <pre className="mt-2 whitespace-pre-wrap text-xs text-slate-300">
                              {JSON.stringify(
                                entry,
                                null,
                                2
                              )}
                            </pre>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold">
                        Human Approvals
                      </h2>

                      <p className="mt-1 text-sm text-slate-400">
                        Risky operations require approval.
                      </p>
                    </div>

                    <button
                      onClick={() =>
                        void loadApprovals(
                          selectedProject.id
                        )
                      }
                      className="text-sm text-cyan-400"
                    >
                      Refresh
                    </button>
                  </div>

                  <button
                    onClick={createRollbackApproval}
                    disabled={loading}
                    className="mt-5 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300 disabled:opacity-50"
                  >
                    Create Rollback Approval
                  </button>

                  <div className="mt-4 space-y-3">
                    {approvals.length === 0 ? (
                      <p className="text-sm text-slate-500">
                        No approval requests.
                      </p>
                    ) : (
                      approvals.map((approval) => (
                        <div
                          key={approval.id}
                          className="rounded-xl border border-slate-800 bg-slate-950 p-4"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium">
                                #{approval.id}{" "}
                                {approval.tool}
                              </p>

                              <p className="mt-1 text-xs text-slate-500">
                                {approval.status}
                              </p>
                            </div>

                            {approval.status ===
                              "pending" && (
                              <button
                                onClick={() =>
                                  approveRollback(
                                    approval.id
                                  )
                                }
                                disabled={loading}
                                className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-50"
                              >
                                Approve
                              </button>
                            )}
                          </div>

                          {approval.result && (
                            <pre className="mt-3 whitespace-pre-wrap text-xs text-slate-400">
                              {JSON.stringify(
                                approval.result,
                                null,
                                2
                              )}
                            </pre>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <h2 className="text-lg font-semibold">
                    DevOps Improvement Report
                  </h2>

                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    <div>
                      <h3 className="font-medium text-cyan-400">
                        Findings
                      </h3>

                      <ul className="mt-2 space-y-2 text-sm text-slate-400">
                        <li>
                          Database connection failures
                        </li>

                        <li>
                          Request failures and HTTP 500
                          errors
                        </li>

                        <li>
                          Unhealthy deployment detected
                        </li>
                      </ul>
                    </div>

                    <div>
                      <h3 className="font-medium text-cyan-400">
                        Recommendations
                      </h3>

                      <ul className="mt-2 space-y-2 text-sm text-slate-400">
                        <li>
                          Validate database configuration
                          in CI
                        </li>

                        <li>
                          Add post-deployment health
                          checks
                        </li>

                        <li>
                          Define rollback thresholds
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </>
            )}
          </section>
        </section>
      </div>
    </main>
  );
}