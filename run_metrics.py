from test_pipeline_movie import test_model_movies_v2
r = test_model_movies_v2()
print("\n" + "=" * 50)
print("FINAL RESULTS SUMMARY:")
for k, v in r.items():
    print(f"  {k}: {v}")
