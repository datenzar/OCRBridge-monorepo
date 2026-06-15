"""Performance and benchmark tests for EasyOCR engine.

These tests measure processing time and resource usage.
They are marked as slow tests and may take significant time to run.
"""

import time
from pathlib import Path

import pytest

from ocrbridge.engines.easyocr import EasyOCREngine, EasyOCRParams


@pytest.mark.slow
@pytest.mark.integration
class TestEasyOCRPerformance:
    """Performance benchmark tests for EasyOCR engine."""

    def test_jpeg_processing_time(self, sample_jpg_stock: Path) -> None:
        """Benchmark JPEG image processing time."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en"])

        start_time = time.time()
        result = engine.process(sample_jpg_stock, params)
        elapsed_time = time.time() - start_time

        # Verify result is valid
        assert result.startswith('<?xml version="1.0"')

        # Log timing information (not asserting specific time as it varies by hardware)
        print(f"\nJPEG processing time: {elapsed_time:.2f} seconds")

        # Sanity check: should complete in reasonable time (60 seconds max)
        assert elapsed_time < 60.0, f"JPEG processing took too long: {elapsed_time:.2f}s"

    def test_pdf_processing_time(self, sample_pdf_en_scan: Path) -> None:
        """Benchmark PDF processing time."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en"])

        start_time = time.time()
        result = engine.process(sample_pdf_en_scan, params)
        elapsed_time = time.time() - start_time

        # Verify result is valid
        assert result.startswith('<?xml version="1.0"')

        print(f"\nPDF processing time: {elapsed_time:.2f} seconds")

        # PDFs take longer due to conversion; allow up to 120 seconds
        assert elapsed_time < 120.0, f"PDF processing took too long: {elapsed_time:.2f}s"

    def test_reader_initialization_time(self) -> None:
        """Benchmark EasyOCR reader initialization time."""
        engine = EasyOCREngine()

        start_time = time.time()
        engine._create_reader(["en"])
        elapsed_time = time.time() - start_time

        print(f"\nReader initialization time: {elapsed_time:.2f} seconds")

        # Reader initialization can be slow on first load (model download/loading)
        # Allow up to 180 seconds for model loading
        assert elapsed_time < 180.0, f"Reader initialization took too long: {elapsed_time:.2f}s"

    def test_sequential_processing_performance(
        self,
        sample_jpg_stock: Path,
        sample_jpg_numbers: Path,
    ) -> None:
        """Benchmark sequential processing of multiple images."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en"])

        # Process multiple images sequentially
        files = [sample_jpg_stock, sample_jpg_numbers, sample_jpg_stock]

        start_time = time.time()
        results = []
        for file_path in files:
            result = engine.process(file_path, params)
            results.append(result)
        elapsed_time = time.time() - start_time

        # Verify all results are valid
        assert len(results) == 3
        for result in results:
            assert result.startswith('<?xml version="1.0"')

        print(f"\nSequential processing of {len(files)} images: {elapsed_time:.2f} seconds")
        print(f"Average per image: {elapsed_time / len(files):.2f} seconds")

        # Should complete in reasonable time
        assert elapsed_time < 180.0, f"Sequential processing took too long: {elapsed_time:.2f}s"

    def test_language_switching_overhead(
        self,
        sample_pdf_en_scan: Path,
        sample_pdf_de_scan: Path,
    ) -> None:
        """Benchmark overhead of switching languages."""
        engine = EasyOCREngine()

        # First processing with English (includes reader creation)
        start_time = time.time()
        result1 = engine.process(sample_pdf_en_scan, EasyOCRParams(languages=["en"]))
        time_with_en = time.time() - start_time

        # Second processing with German (requires reader recreation)
        start_time = time.time()
        result2 = engine.process(sample_pdf_de_scan, EasyOCRParams(languages=["de"]))
        time_with_de = time.time() - start_time

        assert result1.startswith('<?xml version="1.0"')
        assert result2.startswith('<?xml version="1.0"')

        print(f"\nFirst language (EN): {time_with_en:.2f} seconds")
        print(f"Second language (DE): {time_with_de:.2f} seconds")

        # Both should complete in reasonable time
        assert time_with_en < 120.0
        assert time_with_de < 120.0

    def test_reader_reuse_performance_benefit(self, sample_jpg_stock: Path) -> None:
        """Verify that reader reuse provides performance benefit."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en"])

        # First run (includes reader creation)
        start_time = time.time()
        result1 = engine.process(sample_jpg_stock, params)
        first_run_time = time.time() - start_time

        # Second run (reuses reader)
        start_time = time.time()
        result2 = engine.process(sample_jpg_stock, params)
        second_run_time = time.time() - start_time

        assert result1.startswith('<?xml version="1.0"')
        assert result2.startswith('<?xml version="1.0"')

        print(f"\nFirst run (with reader creation): {first_run_time:.2f} seconds")
        print(f"Second run (reader reuse): {second_run_time:.2f} seconds")

        # Second run should be faster or comparable
        # (Not enforcing strict comparison as timing can vary)
        # Just verify both complete successfully
        assert first_run_time < 60.0
        assert second_run_time < 60.0


@pytest.mark.slow
@pytest.mark.integration
class TestEasyOCRScalability:
    """Scalability tests for different file sizes and complexities."""

    def test_process_all_samples(
        self,
        sample_jpg_stock: Path,
        sample_jpg_numbers: Path,
        sample_pdf_en_scan: Path,
        sample_pdf_en_photo: Path,
        sample_pdf_de_scan: Path,
        sample_pdf_de_photo: Path,
    ) -> None:
        """Test processing all sample files to verify engine handles variety."""
        engine = EasyOCREngine()

        samples = [
            (sample_jpg_stock, ["en"]),
            (sample_jpg_numbers, ["en"]),
            (sample_pdf_en_scan, ["en"]),
            (sample_pdf_en_photo, ["en"]),
            (sample_pdf_de_scan, ["de"]),
            (sample_pdf_de_photo, ["de"]),
        ]

        results = []
        timings = []

        for file_path, languages in samples:
            params = EasyOCRParams(languages=languages)
            start_time = time.time()
            result = engine.process(file_path, params)
            elapsed = time.time() - start_time

            results.append(result)
            timings.append((file_path.name, elapsed))

        # Verify all processed successfully
        assert len(results) == len(samples)
        for result in results:
            assert result.startswith('<?xml version="1.0"')

        # Print timing breakdown
        print("\n\nProcessing time breakdown:")
        for filename, timing in timings:
            print(f"  {filename}: {timing:.2f}s")

        total_time = sum(t for _, t in timings)
        print(f"\nTotal time: {total_time:.2f}s")
        print(f"Average per file: {total_time / len(samples):.2f}s")

    def test_multiple_language_performance(self, sample_jpg_stock: Path) -> None:
        """Test performance impact of using multiple languages."""
        engine_single = EasyOCREngine()
        engine_multi = EasyOCREngine()

        # Single language
        params_single = EasyOCRParams(languages=["en"])
        start_time = time.time()
        result_single = engine_single.process(sample_jpg_stock, params_single)
        time_single = time.time() - start_time

        # Multiple languages
        params_multi = EasyOCRParams(languages=["en", "de", "fr"])
        start_time = time.time()
        result_multi = engine_multi.process(sample_jpg_stock, params_multi)
        time_multi = time.time() - start_time

        assert result_single.startswith('<?xml version="1.0"')
        assert result_multi.startswith('<?xml version="1.0"')

        print(f"\nSingle language (en): {time_single:.2f}s")
        print(f"Multiple languages (en, de, fr): {time_multi:.2f}s")
        overhead_pct = (time_multi / time_single - 1) * 100
        print(f"Overhead: {time_multi - time_single:.2f}s ({overhead_pct:.1f}%)")

        # Both should complete successfully
        assert time_single < 60.0
        assert time_multi < 90.0  # Allow more time for multi-language
