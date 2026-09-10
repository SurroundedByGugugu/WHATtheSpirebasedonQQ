"""Focused adapter and static bundle checks; run with python -B web/verify.py."""
import json
import sys
import unittest
import zipfile
from pathlib import Path

WEB = Path(__file__).resolve().parent
sys.path.insert(0, str(WEB.parent))
import bridge
from app.game_service import GameService

class WebChecks(unittest.TestCase):
    def setUp(self):
        bridge.service = GameService()

    def send(self, text):
        return json.loads(bridge.dispatch(text))

    def test_five_characters_and_confirmations(self):
        for index in range(5):
            bridge.service = GameService()
            result = self.send(f"/card new {index}")
            self.assertIsNotNone(result["run"])
            self.assertTrue(result["run"]["choices"])
            old_name = result["run"]["name"]
            self.assertTrue(self.send(f"/card new {(index + 1) % 5}")["confirmation"])
            result = self.send("/card no")
            self.assertFalse(result["confirmation"])
            self.assertEqual(result["run"]["name"], old_name)

    def test_combat_and_turn(self):
        self.send("/card new 0")
        battle = self.send("/card testroom battle")
        self.assertTrue(battle["run"]["battle"])
        self.assertTrue(battle["run"]["hand"])
        self.assertTrue(battle["run"]["enemies"])
        # A deterministic normal attack verifies command dispatch and state refresh.
        self.send("/ctrl addcard 打击 手牌")
        card_index = len(self.send("/card view")["run"]["hand"]) - 1
        result = self.send(f"/card play {card_index} 0")
        self.assertIn("打击", result["reply"])
        self.assertEqual(result["run"]["energy"], 2)
        result = self.send("/card end")
        self.assertEqual(result["run"]["turn"], 2)

    def test_multiplayer_is_rejected(self):
        for command in ("/card multi create", ".card pvp create", "。card 多人", "/CARD PVP"):
            result = self.send(command)
            self.assertIn("仅支持单人", result["reply"])
            self.assertIsNone(result["run"])

    def test_bundle_has_required_files_only(self):
        with zipfile.ZipFile(WEB / "cloudflare-upload.zip") as archive:
            for name in ("index.html", "app.js", "bootstrap.js", "style.css", "worker.js", "engine.zip", "build.json"):
                self.assertIn(name, archive.namelist())
        with zipfile.ZipFile(WEB / "dist" / "engine.zip") as archive:
            self.assertIn("web_bridge.py", archive.namelist())
            self.assertNotIn("main.py", archive.namelist())
            self.assertTrue(all(name.endswith(".py") for name in archive.namelist()))
            self.assertFalse(any("bot_config" in name or ".git" in name for name in archive.namelist()))

if __name__ == "__main__":
    unittest.main()
