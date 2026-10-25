from pathlib import Path
import pytest
from radar import config


def test_normal_clone_accepts_external_private_storage(tmp_path, monkeypatch):
    project=tmp_path/'repos'/'radar'
    project.mkdir(parents=True)
    monkeypatch.setattr(config,'PROJECT',project)
    private=tmp_path/'private-data'
    monkeypatch.setenv('RADAR_PRIVATE_ROOT',str(private))
    assert config.private_root()==private.resolve()


def test_detected_brain_and_project_are_protected(tmp_path, monkeypatch):
    brain=tmp_path/'brain'
    project=brain/'01-projetos'/'radar'
    project.mkdir(parents=True)
    for name in ('MANUAL_DO_BRAIN.md','SEGURANCA.md'):(brain/name).write_text('rules')
    monkeypatch.setattr(config,'PROJECT',project)
    for private in (brain/'private',project/'private',tmp_path/'OneDrive'/'private'):
        monkeypatch.setenv('RADAR_PRIVATE_ROOT',str(private))
        with pytest.raises(ValueError):config.private_root()
