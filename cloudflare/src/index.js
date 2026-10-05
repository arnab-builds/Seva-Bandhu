/**
 * Seva Bandhu Health Monitor Cloudflare Worker
 *
 * Runs on a cron schedule (`*\/10 * * * *`) every 10 minutes.
 * Primary Check:
 *   GET ${HEALTHCHECK_URL} -> Render /health/db/ -> Django -> Supabase PostgreSQL (SELECT 1)
 *
 * Secondary Check:
 *   GET ${SUPABASE_HEALTH_URL} (if configured)
 *
 * Security:
 *   - No database credentials (DATABASE_URL, password)
 *   - No Supabase service-role keys
 *   - No Django secret keys
 *   - No sensitive header logging
 */

async function checkRenderHealth(url) {
  if (!url) {
    return {
      status: "UNHEALTHY",
      detail: "HEALTHCHECK_URL not configured",
      httpStatus: null,
    };
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

    const resp = await fetch(url, {
      method: "GET",
      headers: {
        "User-Agent": "SevaBandhu-HealthMonitor/1.0",
        "Accept": "application/json",
      },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (resp.status === 200) {
      return {
        status: "HEALTHY",
        detail: "HTTP 200 OK",
        httpStatus: 200,
      };
    } else {
      return {
        status: "UNHEALTHY",
        detail: `HTTP ${resp.status}`,
        httpStatus: resp.status,
      };
    }
  } catch (err) {
    return {
      status: "UNHEALTHY",
      detail: err.name === "AbortError" ? "Timeout after 10s" : "Network error / unreachable",
      httpStatus: null,
    };
  }
}

async function checkSupabaseHealth(url, anonKey) {
  if (!url) {
    return {
      status: "NOT_CONFIGURED",
      detail: "SUPABASE_HEALTH_URL not configured; verified via Render /health/db/",
      httpStatus: null,
    };
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

    const headers = {
      "User-Agent": "SevaBandhu-HealthMonitor/1.0",
      "Accept": "application/json",
    };
    if (anonKey) {
      headers["apikey"] = anonKey;
    }

    const resp = await fetch(url, {
      method: "GET",
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (resp.status === 200) {
      return {
        status: "HEALTHY",
        detail: "HTTP 200 OK",
        httpStatus: 200,
      };
    } else {
      return {
        status: "UNHEALTHY",
        detail: `HTTP ${resp.status}`,
        httpStatus: resp.status,
      };
    }
  } catch (err) {
    return {
      status: "UNHEALTHY",
      detail: err.name === "AbortError" ? "Timeout after 10s" : "Network error / unreachable",
      httpStatus: null,
    };
  }
}

export async function runHealthCheck(env) {
  const renderUrl = env?.HEALTHCHECK_URL;
  const supabaseUrl = env?.SUPABASE_HEALTH_URL;
  const supabaseAnonKey = env?.SUPABASE_ANON_KEY;

  // Execute checks independently; failure of one does not abort the other
  const [renderResult, supabaseResult] = await Promise.all([
    checkRenderHealth(renderUrl),
    checkSupabaseHealth(supabaseUrl, supabaseAnonKey),
  ]);

  const timestamp = new Date().toISOString();
  const summary = {
    timestamp,
    render: renderResult.status,
    render_detail: renderResult.detail,
    supabase: supabaseResult.status,
    supabase_detail: supabaseResult.detail,
  };

  // Safe structured logging - never logs auth headers or credentials
  console.log(
    `[HealthCheck] ${timestamp} | Render: ${renderResult.status} (${renderResult.detail}) | Supabase: ${supabaseResult.status} (${supabaseResult.detail})`
  );

  return summary;
}

export default {
  // Cloudflare Cron Scheduled handler
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runHealthCheck(env));
  },

  // HTTP Fetch handler (for on-demand invocation or testing)
  async fetch(request, env, ctx) {
    const summary = await runHealthCheck(env);
    const isHealthy =
      summary.render === "HEALTHY" &&
      (summary.supabase === "HEALTHY" || summary.supabase === "NOT_CONFIGURED");

    return new Response(JSON.stringify(summary, null, 2), {
      status: isHealthy ? 200 : 503,
      headers: { "Content-Type": "application/json" },
    });
  },
};

