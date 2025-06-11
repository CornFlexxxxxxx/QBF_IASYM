#!/usr/bin/env python3
"""
QBF Logic System - Clean Version
Text to QBF conversion with LLM + TweetyProject QBF solving
"""

import subprocess
import tempfile
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QBFResult(Enum):
    SATISFIABLE = "SATISFIABLE"
    UNSATISFIABLE = "UNSATISFIABLE"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"

@dataclass
class QBFFormula:
    formula: str
    variables: List[str]
    quantifiers: List[Tuple[str, str]]
    description: str = None

@dataclass
class QBFEvaluationResult:
    formula: QBFFormula
    result: QBFResult
    execution_time: float
    solver_output: str
    error_message: str = None

class TweetyQBFSolver:
    def __init__(self, jar_path: str):
        self.jar_path = Path(jar_path)
        if not self.jar_path.exists():
            raise FileNotFoundError(f"TweetyProject JAR not found: {jar_path}")
        
        subprocess.run(["java", "-version"], capture_output=True, check=True)
        
        self.bridge_dir = Path("tweety_bridge")
        self.bridge_dir.mkdir(exist_ok=True)
        self._create_bridge()
    
    def _create_bridge(self):
        java_code = '''import org.tweetyproject.logics.qbf.parser.QbfParser;
import org.tweetyproject.logics.qbf.reasoner.NaiveQbfReasoner;
import org.tweetyproject.logics.pl.syntax.PlBeliefSet;
import org.tweetyproject.logics.pl.syntax.PlFormula;
import org.tweetyproject.logics.pl.syntax.Contradiction;
import java.io.*;

public class TweetyQBFBridge {
    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("ERROR: No input provided");
            System.exit(1);
        }
        
        try {
            String qbfContent = args[0];
            
            File tempFile = File.createTempFile("qbf_", ".qbf");
            try (FileWriter writer = new FileWriter(tempFile)) {
                writer.write(qbfContent);
            }
            
            QbfParser parser = new QbfParser();
            PlBeliefSet beliefSet = (PlBeliefSet) parser.parseBeliefBaseFromFile(tempFile.getAbsolutePath());
            
            PlFormula formula = null;
            if (!beliefSet.isEmpty()) {
                formula = beliefSet.iterator().next();
            }
            
            if (formula != null) {
                NaiveQbfReasoner reasoner = new NaiveQbfReasoner();
                Contradiction contradiction = new Contradiction();
                boolean isContradictory = reasoner.query(beliefSet, contradiction);
                
                if (isContradictory) {
                    System.out.println("RESULT: UNSATISFIABLE");
                } else {
                    System.out.println("RESULT: SATISFIABLE");
                }
            } else {
                System.out.println("RESULT: ERROR");
            }
            
            tempFile.delete();
            
        } catch (Exception e) {
            System.out.println("RESULT: ERROR");
        }
    }
}'''
        
        bridge_file = self.bridge_dir / "TweetyQBFBridge.java"
        with open(bridge_file, 'w') as f:
            f.write(java_code)
        
        # Remove old class file
        class_file = self.bridge_dir / "TweetyQBFBridge.class"
        if class_file.exists():
            class_file.unlink()
    
    def _compile_bridge(self):
        try:
            bridge_file = self.bridge_dir / "TweetyQBFBridge.java"
            result = subprocess.run([
                "javac", "-cp", str(self.jar_path), str(bridge_file)
            ], capture_output=True, text=True)
            
            return result.returncode == 0
        except Exception:
            return False
    
    def evaluate_qbf(self, formula: QBFFormula) -> QBFEvaluationResult:
        import time
        start_time = time.time()
        
        try:
            bridge_class = self.bridge_dir / "TweetyQBFBridge.class"
            if not bridge_class.exists():
                if not self._compile_bridge():
                    return self._error_result(formula, start_time, "Compilation failed")
            
            qbf_content = self._to_qbf_format(formula)
            
            cmd = [
                "java", "-cp", f"{self.jar_path}:{self.bridge_dir}",
                "TweetyQBFBridge", qbf_content
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            execution_time = time.time() - start_time
            
            qbf_result = self._parse_output(result.stdout)
            
            return QBFEvaluationResult(
                formula=formula,
                result=qbf_result,
                execution_time=execution_time,
                solver_output=result.stdout,
                error_message=result.stderr if result.stderr else None
            )
            
        except Exception as e:
            return self._error_result(formula, time.time() - start_time, str(e))
    
    def _to_qbf_format(self, formula: QBFFormula) -> str:
        inner_formula = self._convert_formula_syntax(formula.formula)
        result = inner_formula
        for quant_type, var in reversed(formula.quantifiers):
            result = f"{quant_type} {var}: ({result})"
        return result
    
    def _convert_formula_syntax(self, formula: str) -> str:
        return formula.replace("&", " && ").replace("|", " || ").replace("~", "!")
    
    def _error_result(self, formula: QBFFormula, exec_time: float, error: str) -> QBFEvaluationResult:
        return QBFEvaluationResult(formula, QBFResult.ERROR, exec_time, "", error)
    
    def _parse_output(self, stdout: str) -> QBFResult:
        if "RESULT: SATISFIABLE" in stdout:
            return QBFResult.SATISFIABLE
        elif "RESULT: UNSATISFIABLE" in stdout:
            return QBFResult.UNSATISFIABLE
        else:
            return QBFResult.ERROR

class LLMAssistant:
    def __init__(self, api_key: str, api_endpoint: str = "https://api.openai.com/v1/chat/completions"):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
    
    def text_to_qbf(self, text: str) -> QBFFormula:
        prompt = f"""
        Convert this text to a Quantified Boolean Formula (QBF):
        
        Text: {text}
        
        Provide EXACTLY this format:
        Formula: [use &, |, ~, (, ) with simple variables like p, q, r, s]
        Variables: [comma-separated list]
        Quantifiers: [format: "exists p, forall q"]
        
        Example:
        Formula: s & ~s
        Variables: s
        Quantifiers: forall s
        """
        
        response = self._call_llm(prompt)
        return self._parse_qbf_response(response, text)
    
    def _parse_qbf_response(self, response: str, original_text: str) -> QBFFormula:
        try:
            lines = response.split('\n')
            formula = "p"
            variables = ["p"]
            quantifiers = [("exists", "p")]
            
            for line in lines:
                line = line.strip()
                if line.startswith("Formula:"):
                    formula = line.replace("Formula:", "").strip()
                elif line.startswith("Variables:"):
                    vars_str = line.replace("Variables:", "").strip()
                    if vars_str:
                        variables = [v.strip() for v in vars_str.split(",") if v.strip()]
                elif line.startswith("Quantifiers:"):
                    quant_str = line.replace("Quantifiers:", "").strip()
                    quantifiers = []
                    for q in quant_str.split(","):
                        q = q.strip()
                        if "exists" in q:
                            var = q.replace("exists", "").strip()
                            quantifiers.append(("exists", var))
                        elif "forall" in q:
                            var = q.replace("forall", "").strip()
                            quantifiers.append(("forall", var))
            
            if not variables:
                variables = ["p"]
            if not quantifiers:
                quantifiers = [("forall", variables[0])]
                
            return QBFFormula(formula, variables, quantifiers, original_text)
            
        except Exception:
            return QBFFormula("p", ["p"], [("exists", "p")], original_text)
    
    def _call_llm(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.api_endpoint, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return "Formula: p\nVariables: p\nQuantifiers: exists p"

class QBFLogicSystem:
    def __init__(self, jar_path: str, llm_api_key: str):
        self.solver = TweetyQBFSolver(jar_path)
        self.llm = LLMAssistant(llm_api_key)
    
    def evaluate_text(self, text: str) -> Dict[str, Any]:
        qbf_formula = self.llm.text_to_qbf(text)
        result = self.solver.evaluate_qbf(qbf_formula)
        
        return {
            "original_text": text,
            "qbf_formula": qbf_formula.formula,
            "variables": qbf_formula.variables,
            "quantifiers": qbf_formula.quantifiers,
            "result": result.result.value,
            "execution_time": result.execution_time,
            "solver_output": result.solver_output,
            "error": result.error_message
        }
    
    def evaluate_qbf(self, formula_str: str, variables: List[str], 
                     quantifiers: List[Tuple[str, str]]) -> Dict[str, Any]:
        formula = QBFFormula(formula_str, variables, quantifiers)
        result = self.solver.evaluate_qbf(formula)
        
        return {
            "formula": formula_str,
            "result": result.result.value,
            "execution_time": result.execution_time,
            "solver_output": result.solver_output,
            "error": result.error_message
        }

def main():
    from config import Config
    
    try:
        system = QBFLogicSystem(
            jar_path=str(Config.JAR_PATH),
            llm_api_key=Config.get_api_key()
        )
        
        print("=== QBF Logic System ===")
        
        # Test text conversion
        result = system.evaluate_text("Every student either passes or fails")
        print(f"Text: Every student either passes or fails")
        print(f"QBF: {result['qbf_formula']}")
        print(f"Result: {result['result']}")
        
        # Test direct QBF
        result = system.evaluate_qbf("x | ~x", ["x"], [("forall", "x")])
        print(f"\nDirect QBF: ∀x (x ∨ ¬x)")
        print(f"Result: {result['result']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()