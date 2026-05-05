import io
import sys

from compiler.__main__ import main
from pytest import CaptureFixture, MonkeyPatch


def test_documented_interpret_command_runs_interpreter(
        monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, 'argv', ['main', 'interpret'])
    monkeypatch.setattr(sys, 'stdin', io.StringIO('1 + 2'))

    assert main() == 0

    captured = capsys.readouterr()
    assert captured.out == '3\n'
