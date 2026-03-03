"""Tests for CLI argument parsing and behavior."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from agent_harness.cli import main


class TestCLI:
    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_prompt_is_required(self) -> None:
        result = self.runner.invoke(main, [])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_help_flag(self) -> None:
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--prompt" in result.output
        assert "--cwd" in result.output
        assert "--output" in result.output
        assert "--resume" in result.output
        assert "--permission-mode" in result.output

    @patch("agent_harness.cli.run_agent_sync")
    @patch("agent_harness.cli.resolve_provider")
    @patch("agent_harness.cli.discover_skills")
    @patch("agent_harness.cli.load_config")
    def test_prompt_passes_through(
        self,
        mock_config: MagicMock,
        mock_skills: MagicMock,
        mock_provider: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        from agent_harness.agent import AgentResult
        from agent_harness.config import HarnessConfig
        from agent_harness.providers import ProviderConfig

        mock_config.return_value = HarnessConfig()
        mock_skills.return_value = []
        mock_provider.return_value = ProviderConfig(
            provider="anthropic", model="test", env={"ANTHROPIC_API_KEY": "sk-test"}
        )
        mock_run.return_value = AgentResult(response_text="hello", session_id=None, exit_code=0)

        result = self.runner.invoke(main, ["--prompt", "test prompt"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs[1]["prompt"] == "test prompt" or call_kwargs[0][0] == "test prompt"

    @patch("agent_harness.cli.run_agent_sync")
    @patch("agent_harness.cli.resolve_provider")
    @patch("agent_harness.cli.discover_skills")
    @patch("agent_harness.cli.load_config")
    def test_cwd_passes_through(
        self,
        mock_config: MagicMock,
        mock_skills: MagicMock,
        mock_provider: MagicMock,
        mock_run: MagicMock,
        tmp_path: MagicMock,
    ) -> None:
        from agent_harness.agent import AgentResult
        from agent_harness.config import HarnessConfig
        from agent_harness.providers import ProviderConfig

        mock_config.return_value = HarnessConfig()
        mock_skills.return_value = []
        mock_provider.return_value = ProviderConfig(
            provider="anthropic", model="test", env={"ANTHROPIC_API_KEY": "sk-test"}
        )
        mock_run.return_value = AgentResult(response_text="", session_id=None, exit_code=0)

        result = self.runner.invoke(main, ["--prompt", "test", "--cwd", str(tmp_path)])
        assert result.exit_code == 0

    @patch("agent_harness.cli.run_agent_sync")
    @patch("agent_harness.cli.resolve_provider")
    @patch("agent_harness.cli.discover_skills")
    @patch("agent_harness.cli.load_config")
    def test_json_output_format(
        self,
        mock_config: MagicMock,
        mock_skills: MagicMock,
        mock_provider: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        import json

        from agent_harness.agent import AgentResult
        from agent_harness.config import HarnessConfig
        from agent_harness.providers import ProviderConfig

        mock_config.return_value = HarnessConfig()
        mock_skills.return_value = []
        mock_provider.return_value = ProviderConfig(
            provider="anthropic", model="test", env={"ANTHROPIC_API_KEY": "sk-test"}
        )
        mock_run.return_value = AgentResult(
            response_text="result text", session_id="sess-123", exit_code=0
        )

        result = self.runner.invoke(main, ["--prompt", "test", "--output", "json"])
        assert result.exit_code == 0
        output = json.loads(result.output.strip())
        assert output["type"] == "result"
        assert output["payload"]["response_text"] == "result text"
        assert output["payload"]["session_id"] == "sess-123"

    @patch("agent_harness.cli.run_agent_sync")
    @patch("agent_harness.cli.resolve_provider")
    @patch("agent_harness.cli.discover_skills")
    @patch("agent_harness.cli.load_config")
    def test_resume_passes_session_id(
        self,
        mock_config: MagicMock,
        mock_skills: MagicMock,
        mock_provider: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        from agent_harness.agent import AgentResult
        from agent_harness.config import HarnessConfig
        from agent_harness.providers import ProviderConfig

        mock_config.return_value = HarnessConfig()
        mock_skills.return_value = []
        mock_provider.return_value = ProviderConfig(
            provider="anthropic", model="test", env={"ANTHROPIC_API_KEY": "sk-test"}
        )
        mock_run.return_value = AgentResult(response_text="", session_id=None, exit_code=0)

        result = self.runner.invoke(main, ["--prompt", "test", "--resume", "session-abc"])
        assert result.exit_code == 0
        call_kwargs = mock_run.call_args
        assert call_kwargs[1].get("resume") == "session-abc" or "session-abc" in str(call_kwargs)

    @patch("agent_harness.cli.run_agent_sync")
    @patch("agent_harness.cli.resolve_provider")
    @patch("agent_harness.cli.discover_skills")
    @patch("agent_harness.cli.load_config")
    def test_permission_mode_override(
        self,
        mock_config: MagicMock,
        mock_skills: MagicMock,
        mock_provider: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        from agent_harness.agent import AgentResult
        from agent_harness.config import HarnessConfig
        from agent_harness.providers import ProviderConfig

        mock_config.return_value = HarnessConfig()
        mock_skills.return_value = []
        mock_provider.return_value = ProviderConfig(
            provider="anthropic", model="test", env={"ANTHROPIC_API_KEY": "sk-test"}
        )
        mock_run.return_value = AgentResult(response_text="", session_id=None, exit_code=0)

        result = self.runner.invoke(main, ["--prompt", "test", "--permission-mode", "plan"])
        assert result.exit_code == 0

    def test_invalid_output_format(self) -> None:
        result = self.runner.invoke(main, ["--prompt", "test", "--output", "xml"])
        assert result.exit_code != 0

    @patch("agent_harness.cli.resolve_provider")
    @patch("agent_harness.cli.load_config")
    def test_provider_error_exits_nonzero(
        self,
        mock_config: MagicMock,
        mock_provider: MagicMock,
    ) -> None:
        from agent_harness.config import HarnessConfig
        from agent_harness.providers import ProviderError

        mock_config.return_value = HarnessConfig()
        mock_provider.side_effect = ProviderError("Missing API key")

        result = self.runner.invoke(main, ["--prompt", "test"])
        assert result.exit_code != 0
        assert "Provider error" in result.output or "Missing API key" in result.output
