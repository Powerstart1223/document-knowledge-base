Set-Location 'C:\Users\SJK\document-knowledge-base';
  $env:SEC_EDGAR_USER_AGENT='Your Name your@email.com'; & 'C:\Users\SJK\AppData\Local\Programs\Python\Python313\python.exe' 'finetune\continuous_weight_improvement.py' --scan-drives --include-uploads --include-edgar --fallback
  *>> 'C:\Users\SJK\document-knowledge-base\logs\true_weight_improvement.log'
