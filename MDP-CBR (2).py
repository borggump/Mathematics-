import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import datetime
from typing import Dict, List, Tuple
import math
import random

class Case:
    """Represents a case in the Case Bank"""
    def __init__(self, task_id: str, task_description: str, context: str, 
                 actions: List[str], outcome: str, success: bool, timestamp: str):
        self.task_id = task_id
        self.task_description = task_description
        self.context = context
        self.actions = actions
        self.outcome = outcome
        self.success = success
        self.timestamp = timestamp
        self.usage_count = 0
        self.success_rate = 1.0 if success else 0.0

class CBREngine:
    """Case-Based Reasoning Engine"""
    def __init__(self):
        self.case_bank = []
        self.similarity_threshold = 0.3
    
    def add_case(self, case: Case):
        """Add a new case to the case bank"""
        self.case_bank.append(case)
    
    def calculate_similarity(self, query: str, case: Case) -> float:
        """Simple similarity calculation based on word overlap"""
        query_words = set(query.lower().split())
        case_words = set(case.task_description.lower().split())
        
        if not query_words or not case_words:
            return 0.0
        
        intersection = query_words.intersection(case_words)
        union = query_words.union(case_words)
        
        jaccard_sim = len(intersection) / len(union) if union else 0.0
        
        # Boost similarity for successful cases
        success_boost = 0.1 if case.success else 0.0
        
        # Boost for frequently used cases
        usage_boost = min(0.1, case.usage_count * 0.02)
        
        return min(1.0, jaccard_sim + success_boost + usage_boost)
    
    def retrieve_cases(self, query: str, top_k: int = 3) -> List[Tuple[Case, float]]:
        """Retrieve most similar cases"""
        similarities = []
        
        for case in self.case_bank:
            sim = self.calculate_similarity(query, case)
            if sim >= self.similarity_threshold:
                similarities.append((case, sim))
        
        # Sort by similarity (descending) and success rate
        similarities.sort(key=lambda x: (x[1], x[0].success_rate), reverse=True)
        
        return similarities[:top_k]

class MomentoAgent:
    """Main M-MDP Agent implementing the Memento framework"""
    def __init__(self):
        self.cbr_engine = CBREngine()
        self.current_task = None
        self.execution_history = []
        self.learning_enabled = True
        
        # Initialize with some sample cases
        self._initialize_sample_cases()
    
    def _initialize_sample_cases(self):
        """Add some sample cases to demonstrate the system"""
        sample_cases = [
            Case("001", "research market trends", "financial analysis", 
                 ["search web", "analyze data", "create report"], 
                 "comprehensive market analysis completed", True,
                 "2024-01-15 10:30:00"),
            Case("002", "debug connection error", "software troubleshooting",
                 ["check logs", "test network", "restart service"],
                 "connection restored successfully", True,
                 "2024-01-16 14:20:00"),
            Case("003", "create customer presentation", "sales support",
                 ["gather requirements", "design slides", "review with team"],
                 "presentation delivered on time", True,
                 "2024-01-17 09:15:00"),
            Case("004", "analyze competitor pricing", "market research",
                 ["collect pricing data", "compare features", "identify gaps"],
                 "pricing strategy recommendations provided", True,
                 "2024-01-18 11:45:00"),
        ]
        
        for case in sample_cases:
            self.cbr_engine.add_case(case)
    
    def plan_task(self, task_description: str, context: str = "") -> Dict:
        """Planning phase using CBR to retrieve relevant cases"""
        # Retrieve similar cases
        similar_cases = self.cbr_engine.retrieve_cases(task_description)
        
        # Generate plan based on retrieved cases
        plan = {
            "task": task_description,
            "context": context,
            "retrieved_cases": similar_cases,
            "suggested_actions": self._generate_plan_from_cases(similar_cases),
            "confidence": self._calculate_confidence(similar_cases)
        }
        
        return plan
    
    def _generate_plan_from_cases(self, cases: List[Tuple[Case, float]]) -> List[str]:
        """Generate action plan based on retrieved cases"""
        if not cases:
            return ["analyze task", "research approach", "execute solution", "verify results"]
        
        # Weight actions by similarity and success
        action_weights = {}
        
        for case, similarity in cases:
            weight = similarity * (1.0 if case.success else 0.5)
            for action in case.actions:
                action_weights[action] = action_weights.get(action, 0) + weight
        
        # Sort actions by weight and return top ones
        sorted_actions = sorted(action_weights.items(), key=lambda x: x[1], reverse=True)
        return [action for action, weight in sorted_actions[:4]]
    
    def _calculate_confidence(self, cases: List[Tuple[Case, float]]) -> float:
        """Calculate confidence based on retrieved cases"""
        if not cases:
            return 0.2
        
        total_weight = sum(similarity for _, similarity in cases)
        success_weight = sum(similarity for case, similarity in cases if case.success)
        
        return min(0.95, success_weight / total_weight if total_weight > 0 else 0.2)
    
    def execute_task(self, plan: Dict, actual_actions: List[str], success: bool) -> str:
        """Execute task and store experience"""
        task_id = f"{len(self.cbr_engine.case_bank) + 1:03d}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        outcome = "Task completed successfully" if success else "Task failed or incomplete"
        
        # Create new case
        new_case = Case(
            task_id=task_id,
            task_description=plan["task"],
            context=plan["context"],
            actions=actual_actions,
            outcome=outcome,
            success=success,
            timestamp=timestamp
        )
        
        # Add to case bank for learning
        if self.learning_enabled:
            self.cbr_engine.add_case(new_case)
            
            # Update usage count for retrieved cases
            for case, similarity in plan["retrieved_cases"]:
                case.usage_count += 1
        
        return f"Task {task_id} executed. Case stored for future learning."

class MomentoGUI:
    """GUI Application for the Memento Framework"""
    def __init__(self, root):
        self.root = root
        self.root.title("Memento: M-MDP Framework & CBR Engine Simulator")
        self.root.geometry("1200x800")
        
        self.agent = MomentoAgent()
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Memento: M-MDP Framework Simulator", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel - Input
        input_frame = ttk.LabelFrame(main_frame, text="Task Input", padding="10")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Task description
        ttk.Label(input_frame, text="Task Description:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.task_entry = tk.Text(input_frame, height=3, width=40, wrap=tk.WORD)
        self.task_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Context
        ttk.Label(input_frame, text="Context (optional):").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.context_entry = tk.Text(input_frame, height=2, width=40, wrap=tk.WORD)
        self.context_entry.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Plan button
        self.plan_button = ttk.Button(input_frame, text="Generate Plan (CBR)", command=self.generate_plan)
        self.plan_button.grid(row=4, column=0, pady=(0, 10))
        
        # Actions taken
        ttk.Label(input_frame, text="Actions Taken:").grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        self.actions_entry = tk.Text(input_frame, height=3, width=40, wrap=tk.WORD)
        self.actions_entry.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Success checkbox
        self.success_var = tk.BooleanVar(value=True)
        success_check = ttk.Checkbutton(input_frame, text="Task Successful", variable=self.success_var)
        success_check.grid(row=7, column=0, sticky=tk.W, pady=(0, 10))
        
        # Execute button
        self.execute_button = ttk.Button(input_frame, text="Execute & Learn", command=self.execute_task)
        self.execute_button.grid(row=8, column=0, pady=(0, 10))
        self.execute_button.config(state=tk.DISABLED)
        
        # Right panel - Output
        output_frame = ttk.LabelFrame(main_frame, text="System Output", padding="10")
        output_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, width=60, height=20)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bottom panel - Case Bank
        case_frame = ttk.LabelFrame(main_frame, text="Case Bank Viewer", padding="10")
        case_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        case_frame.columnconfigure(0, weight=1)
        case_frame.rowconfigure(1, weight=1)
        
        # Case bank controls
        controls_frame = ttk.Frame(case_frame)
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(controls_frame, text="View All Cases", command=self.view_cases).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls_frame, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=(0, 10))
        
        # Case bank display
        self.case_text = scrolledtext.ScrolledText(case_frame, wrap=tk.WORD, height=8)
        self.case_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initialize display
        self.display_welcome_message()
        self.view_cases()
    
    def display_welcome_message(self):
        """Display welcome message and instructions"""
        welcome_msg = """🧠 MEMENTO: M-MDP Framework & CBR Engine Simulator

This simulation demonstrates how the Memento framework works:

1. M-MDP (Memory-augmented Markov Decision Process):
   - Agents use external memory instead of fine-tuning
   - Continuous learning without parameter updates
   - Experience-based decision making

2. CBR (Case-Based Reasoning) Engine:
   - Retrieves similar past experiences
   - Adapts solutions based on context
   - Learns from success patterns

HOW TO USE:
1. Enter a task description (e.g., "analyze customer feedback")
2. Add context if needed
3. Click "Generate Plan" to see CBR in action
4. Enter what actions were actually taken
5. Mark success/failure and click "Execute & Learn"
6. Watch the system learn and improve over time!

The system starts with sample cases. Try tasks like:
- "research market trends"
- "debug system error" 
- "create business report"
- "analyze competitor data"

═══════════════════════════════════════════════════════
"""
        self.output_text.insert(tk.END, welcome_msg)
    
    def generate_plan(self):
        """Generate plan using CBR engine"""
        task = self.task_entry.get("1.0", tk.END).strip()
        context = self.context_entry.get("1.0", tk.END).strip()
        
        if not task:
            messagebox.showwarning("Input Required", "Please enter a task description.")
            return
        
        # Generate plan
        plan = self.agent.plan_task(task, context)
        
        # Display results
        output = f"\n🔍 CBR ANALYSIS FOR: '{task}'\n"
        output += "=" * 60 + "\n\n"
        
        if plan["retrieved_cases"]:
            output += f"📚 RETRIEVED CASES ({len(plan['retrieved_cases'])} found):\n"
            for i, (case, similarity) in enumerate(plan["retrieved_cases"], 1):
                output += f"\n{i}. Case #{case.task_id} (Similarity: {similarity:.2f})\n"
                output += f"   Task: {case.task_description}\n"
                output += f"   Actions: {', '.join(case.actions)}\n"
                output += f"   Success: {'✅' if case.success else '❌'} | Used: {case.usage_count} times\n"
        else:
            output += "📚 No similar cases found in memory. Using default approach.\n"
        
        output += f"\n🎯 SUGGESTED ACTION PLAN (Confidence: {plan['confidence']:.1%}):\n"
        for i, action in enumerate(plan["suggested_actions"], 1):
            output += f"{i}. {action}\n"
        
        output += f"\n💡 SYSTEM REASONING:\n"
        if plan["retrieved_cases"]:
            output += f"Based on {len(plan['retrieved_cases'])} similar past experiences, "
            output += f"the system suggests actions that have proven successful before.\n"
        else:
            output += "No prior experience available. Using general problem-solving approach.\n"
        
        output += "\nNext: Enter the actions you actually took and mark success/failure.\n"
        output += "═" * 60 + "\n"
        
        self.output_text.insert(tk.END, output)
        self.output_text.see(tk.END)
        
        # Store current plan for execution
        self.current_plan = plan
        self.execute_button.config(state=tk.NORMAL)
        
        # Auto-populate suggested actions
        suggested_text = "\n".join(plan["suggested_actions"])
        self.actions_entry.delete("1.0", tk.END)
        self.actions_entry.insert("1.0", suggested_text)
    
    def execute_task(self):
        """Execute task and learn from experience"""
        if not hasattr(self, 'current_plan'):
            messagebox.showwarning("Plan Required", "Please generate a plan first.")
            return
        
        actions_text = self.actions_entry.get("1.0", tk.END).strip()
        if not actions_text:
            messagebox.showwarning("Actions Required", "Please enter the actions taken.")
            return
        
        actions = [action.strip() for action in actions_text.split('\n') if action.strip()]
        success = self.success_var.get()
        
        # Execute and learn
        result = self.agent.execute_task(self.current_plan, actions, success)
        
        # Display results
        output = f"\n⚡ TASK EXECUTION COMPLETE\n"
        output += "=" * 60 + "\n"
        output += f"Task: {self.current_plan['task']}\n"
        output += f"Actions Taken: {', '.join(actions)}\n"
        output += f"Outcome: {'✅ SUCCESS' if success else '❌ FAILURE'}\n"
        output += f"Learning: {result}\n\n"
        
        output += "🧠 M-MDP LEARNING PROCESS:\n"
        output += "1. Experience stored in case bank\n"
        output += "2. Future similar tasks will reference this case\n"
        output += "3. System continuously improves without retraining\n"
        if self.current_plan['retrieved_cases']:
            output += f"4. Updated usage statistics for {len(self.current_plan['retrieved_cases'])} retrieved cases\n"
        
        output += f"\n📊 CASE BANK SIZE: {len(self.agent.cbr_engine.case_bank)} cases\n"
        output += "═" * 60 + "\n"
        
        self.output_text.insert(tk.END, output)
        self.output_text.see(tk.END)
        
        # Reset form
        self.task_entry.delete("1.0", tk.END)
        self.context_entry.delete("1.0", tk.END)
        self.actions_entry.delete("1.0", tk.END)
        self.execute_button.config(state=tk.DISABLED)
        
        # Update case bank view
        self.view_cases()
    
    def view_cases(self):
        """Display all cases in the case bank"""
        self.case_text.delete("1.0", tk.END)
        
        if not self.agent.cbr_engine.case_bank:
            self.case_text.insert(tk.END, "No cases in the bank yet.")
            return
        
        header = f"📦 CASE BANK ({len(self.agent.cbr_engine.case_bank)} cases)\n"
        header += "=" * 80 + "\n\n"
        self.case_text.insert(tk.END, header)
        
        for case in self.agent.cbr_engine.case_bank:
            case_info = f"Case #{case.task_id} - {case.timestamp}\n"
            case_info += f"Task: {case.task_description}\n"
            case_info += f"Context: {case.context or 'None'}\n"
            case_info += f"Actions: {', '.join(case.actions)}\n"
            case_info += f"Outcome: {case.outcome}\n"
            case_info += f"Success: {'✅' if case.success else '❌'} | "
            case_info += f"Usage Count: {case.usage_count}\n"
            case_info += "-" * 80 + "\n\n"
            
            self.case_text.insert(tk.END, case_info)
    
    def clear_output(self):
        """Clear the output text area"""
        self.output_text.delete("1.0", tk.END)
        self.display_welcome_message()

def main():
    root = tk.Tk()
    app = MomentoGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()