"""Regression tests for safety, actual alpha, configuration and stage cache."""
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image, ImageDraw
from workflow import cached, digest, fingerprint, protect, sync_template
from prepare_config import prepare
from validate_assets import validate
from batch import projects

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def assets(self):
        assets = self.root / 'assets'
        assets.mkdir()
        im = Image.new('RGBA', (256, 384))
        ImageDraw.Draw(im).rectangle((80, 90, 180, 290), fill=(100, 90, 80, 255))
        for name in ['subject', 'text']:
            im.save(assets / (name + '.png'))
        Image.new('RGB', im.size, 'navy').save(assets / 'background.png')
        line = Image.new('RGB', im.size, 'white')
        ImageDraw.Draw(line).rectangle((80, 90, 180, 290), outline='black', width=2)
        line.save(assets / 'lineart.png')
        return assets

    def test_valid_layers(self):
        self.assets()
        report = validate(self.root)
        self.assertEqual(report['lineart']['outside_subject_fraction'], 0)

    def test_fake_transparency_rejected(self):
        a = self.assets()
        Image.new('RGB', (256, 384), 'gray').save(a / 'subject.png')
        with self.assertRaisesRegex(ValueError, 'alpha'):
            validate(self.root)

    def test_empty_subject_rejected(self):
        a = self.assets()
        Image.new('RGBA', (256, 384)).save(a / 'subject.png')
        with self.assertRaises(ValueError):
            validate(self.root)

    def test_mismatched_dimensions_rejected(self):
        a = self.assets()
        Image.new('RGB', (260, 384)).save(a / 'background.png')
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            validate(self.root)

    def test_dark_line_background_rejected(self):
        a = self.assets()
        im = Image.new('RGB', (256, 384), 'black')
        im.putpixel((0, 0), (255, 255, 255))
        im.save(a / 'lineart.png')
        with self.assertRaisesRegex(ValueError, 'mostly white'):
            validate(self.root)

    def test_config_does_not_overwrite(self):
        first = prepare(self.root, 'My card', 'portrait')
        with self.assertRaises(FileExistsError):
            prepare(self.root, 'Overwrite')
        self.assertEqual(json.loads((self.root / 'card-config.json').read_text()), first)
        self.assertEqual(first['safeArea']['scale'], [.72, .8])

    def test_cache_checks_actual_output(self):
        f = self.root / 'test.txt'
        f.write_text('one')
        entry = {'key': 'abc', 'outputs': {'test.txt': digest(f)}}
        self.assertTrue(cached(entry, 'abc', self.root))
        self.assertFalse(cached(entry, 'different', self.root))
        f.write_text('modified')
        self.assertFalse(cached(entry, 'abc', self.root))

    def test_changed_input_invalidates_hash(self):
        f = self.root / 'input.txt'
        f.write_text('a')
        old = fingerprint([f])
        f.write_text('b')
        self.assertNotEqual(old, fingerprint([f]))

    def test_template_update_and_customization(self):
        src, dest = self.root / 'src', self.root / 'dest'
        src.mkdir()
        (src / 'app.js').write_text('v1')
        sync_template(src, dest)
        (src / 'app.js').write_text('v2')
        sync_template(src, dest)
        self.assertEqual((dest / 'app.js').read_text(), 'v2')
        (dest / 'app.js').write_text('custom')
        with self.assertRaises(FileExistsError):
            sync_template(src, dest)
        self.assertEqual((dest / 'app.js').read_text(), 'custom')
        sync_template(src, dest, replace=True)
        backups = list((dest / '.holo-backups').glob('*/app.js'))
        self.assertEqual(backups[0].read_text(), 'custom')

    def test_unmanaged_scene_is_protected(self):
        f = self.root / 'card.blend'
        f.write_text('user scene')
        with self.assertRaises(FileExistsError):
            protect(self.root, [f], {})
        protect(self.root, [f], {}, replace=True)
        self.assertEqual(next((self.root / '.holo-backups').glob('*/card.blend')).read_text(), 'user scene')

    def test_runtime_config_not_overwritten_by_template(self):
        src, dest = self.root / 'src', self.root / 'dest'
        src.mkdir();dest.mkdir()
        (src / 'card-config.json').write_text('template')
        (dest / 'card-config.json').write_text('user metadata')
        sync_template(src, dest)
        self.assertEqual((dest / 'card-config.json').read_text(), 'user metadata')

    def test_batch_cannot_escape_root(self):
        manifest = self.root / 'batch.json'
        manifest.write_text(json.dumps({'projects': ['../escape']}))
        with self.assertRaises(ValueError):
            projects(manifest)

    def test_batch_duplicate_resolved_path_rejected(self):
        manifest = self.root / 'batch.json'
        manifest.write_text(json.dumps({'projects': ['cards/01', 'cards/../cards/01']}))
        with self.assertRaises(ValueError):
            projects(manifest)

if __name__ == '__main__':
    unittest.main()
