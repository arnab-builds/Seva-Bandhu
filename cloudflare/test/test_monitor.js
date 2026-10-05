import assert from "node:assert";
import { runHealthCheck } from "../src/index.js";

async function runTests() {
  console.log("Starting Cloudflare Health Monitor Worker Tests...\n");

  const originalFetch = globalThis.fetch;

  try {
    // --- CASE 1: Render 200, Supabase 200 ---
    {
      globalThis.fetch = async (url) => {
        if (url.includes("render")) {
          return { status: 200 };
        }
        if (url.includes("supabase")) {
          return { status: 200 };
        }
        return { status: 404 };
      };

      const env = {
        HEALTHCHECK_URL: "https://mock.onrender.com/health/db/",
        SUPABASE_HEALTH_URL: "https://mock.supabase.co/rest/v1/",
      };

      const result = await runHealthCheck(env);
      assert.strictEqual(result.render, "HEALTHY", "Case 1: Render should be HEALTHY");
      assert.strictEqual(result.supabase, "HEALTHY", "Case 1: Supabase should be HEALTHY");
      console.log("PASS: Case 1 - Render 200, Supabase 200 -> Render: HEALTHY, Supabase: HEALTHY");
    }

    // --- CASE 2: Render 503, Supabase 200 ---
    {
      globalThis.fetch = async (url) => {
        if (url.includes("render")) {
          return { status: 503 };
        }
        if (url.includes("supabase")) {
          return { status: 200 };
        }
        return { status: 404 };
      };

      const env = {
        HEALTHCHECK_URL: "https://mock.onrender.com/health/db/",
        SUPABASE_HEALTH_URL: "https://mock.supabase.co/rest/v1/",
      };

      const result = await runHealthCheck(env);
      assert.strictEqual(result.render, "UNHEALTHY", "Case 2: Render should be UNHEALTHY");
      assert.strictEqual(result.supabase, "HEALTHY", "Case 2: Supabase should be HEALTHY");
      console.log("PASS: Case 2 - Render 503, Supabase 200 -> Render: UNHEALTHY, Supabase: HEALTHY");
    }

    // --- CASE 3: Render 200, Supabase 503 ---
    {
      globalThis.fetch = async (url) => {
        if (url.includes("render")) {
          return { status: 200 };
        }
        if (url.includes("supabase")) {
          return { status: 503 };
        }
        return { status: 404 };
      };

      const env = {
        HEALTHCHECK_URL: "https://mock.onrender.com/health/db/",
        SUPABASE_HEALTH_URL: "https://mock.supabase.co/rest/v1/",
      };

      const result = await runHealthCheck(env);
      assert.strictEqual(result.render, "HEALTHY", "Case 3: Render should be HEALTHY");
      assert.strictEqual(result.supabase, "UNHEALTHY", "Case 3: Supabase should be UNHEALTHY");
      console.log("PASS: Case 3 - Render 200, Supabase 503 -> Render: HEALTHY, Supabase: UNHEALTHY");
    }

    // --- CASE 4: Both unavailable (network error / rejected promise) ---
    {
      globalThis.fetch = async () => {
        throw new Error("Connection refused");
      };

      const env = {
        HEALTHCHECK_URL: "https://mock.onrender.com/health/db/",
        SUPABASE_HEALTH_URL: "https://mock.supabase.co/rest/v1/",
      };

      const result = await runHealthCheck(env);
      assert.strictEqual(result.render, "UNHEALTHY", "Case 4: Render should be UNHEALTHY");
      assert.strictEqual(result.supabase, "UNHEALTHY", "Case 4: Supabase should be UNHEALTHY");
      console.log("PASS: Case 4 - Both unavailable -> Render: UNHEALTHY, Supabase: UNHEALTHY");
    }

    // --- CASE 5: Independent Supabase check unconfigured ---
    {
      globalThis.fetch = async (url) => {
        if (url.includes("render")) {
          return { status: 200 };
        }
        return { status: 404 };
      };

      const env = {
        HEALTHCHECK_URL: "https://mock.onrender.com/health/db/",
        // SUPABASE_HEALTH_URL omitted
      };

      const result = await runHealthCheck(env);
      assert.strictEqual(result.render, "HEALTHY", "Case 5: Render should be HEALTHY");
      assert.strictEqual(result.supabase, "NOT_CONFIGURED", "Case 5: Supabase should be NOT_CONFIGURED");
      console.log("PASS: Case 5 - Supabase unconfigured -> Render: HEALTHY, Supabase: NOT_CONFIGURED");
    }

    console.log("\nALL 5 TEST CASES PASSED SUCCESSFULLY!");
  } finally {
    globalThis.fetch = originalFetch;
  }
}

runTests();

