import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_dpo_git_push_logic(client: TestClient):
    """
    /record_preference 호출 시 Git 관련 함수들이 올바른 순서로 호출되는지 테스트
    """
    # git.Repo와 관련된 모든 객체와 메서드를 모킹
    mock_repo_instance = MagicMock()
    mock_origin = MagicMock()
    mock_repo_instance.remote.return_value = mock_origin

    # patch 데코레이터를 사용하여 git.Repo 클래스를 mock_repo_class로 대체
    with patch('main.git.Repo', return_value=mock_repo_instance) as mock_repo_class, \
         patch('main.Path.exists', return_value=True): # 로컬 저장소가 이미 존재한다고 가정

        test_payload = {
            "uo_id": "UHW010",
            "section": "Method",
            "chosen_original": "AI suggestion",
            "chosen_edited": "User edited suggestion",
            "rejected": [],
            "query": "Test query",
            "file_content": "### [UHW010 Liquid Handling]",
            "file_path": "/test/path/001_WF_Test.md",
            "supervisor_evaluations": []
        }

        # API 호출
        response = client.post("/record_preference", json=test_payload)

        # 응답 상태 코드 확인
        assert response.status_code == 204

        # Git 관련 함수 호출 순서 및 내용 검증
        # 1. Repo 객체가 로컬 경로로 초기화되었는지 확인
        mock_repo_class.assert_called_once()

        # 2. git pull (remotes.origin.pull)이 호출되었는지 확인
        mock_repo_instance.remotes.origin.pull.assert_called_once()

        # 3. git add (index.add)가 호출되었는지 확인
        mock_repo_instance.index.add.assert_called_once()

        # 4. git commit (index.commit)이 호출되었는지 확인
        mock_repo_instance.index.commit.assert_called_with("feat: Add DPO data for UHW010/Method")

        # 5. git push (remote().push)가 호출되었는지 확인
        mock_origin.push.assert_called_once()