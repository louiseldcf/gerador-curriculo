import { useState, ChangeEvent, FormEvent } from "react";
import axios from "axios";
import { Card, CardFooter, CardHeader, CardContent } from "./components/ui/card";
import { Label } from "./components/ui/label";
import { Input } from "./components/ui/input";
import { Button } from "./components/ui/button";
import { Textarea } from "./components/ui/textarea";

interface Experience {
  position: string;
  company: string;
  start_year: string;
  end_year: string;
  description: string;
}

interface FormData {
  name: string;
  contact: string;
  experience: Experience[];
  skills: string;
}

function App() {
  const [formData, setFormData] = useState<FormData>({
    name: "",
    contact: "",
    experience: [
      {
        position: "",
        company: "",
        start_year: "",
        end_year: "",
        description: "",
      },
    ],
    skills: "",
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleExperienceChange = (
    index: number,
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    const newExperience = [...formData.experience];
    newExperience[index][name as keyof Experience] = value;
    setFormData({ ...formData, experience: newExperience });
  };

  const addExperience = () => {
    setFormData({
      ...formData,
      experience: [
        ...formData.experience,
        {
          position: "",
          company: "",
          start_year: "",
          end_year: "",
          description: "",
        },
      ],
    });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(
        "http://localhost:5000/process-cv",
        formData,
        {
          responseType: "blob",
        }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "curriculo_gerado.pdf");
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error("Erro ao enviar dados:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App p-6 bg-gray-100 min-h-screen">
      {loading && (
        <div className="fixed inset-0 flex items-center justify-center bg-gray-800 bg-opacity-75 z-50">
          <div className="text-white text-xl">Gerando currículo...</div>
        </div>
      )}
      <Card className="max-w-3xl mx-auto">
        <CardHeader>
          <h1 className="text-2xl font-bold">Gerador de Currículo</h1>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="name">Nome:</Label>
              <Input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="Seu nome"
                disabled={loading}
              />
            </div>
            <div>
              <Label htmlFor="contact">Contato:</Label>
              <Input
                type="email"
                name="contact"
                value={formData.contact}
                onChange={handleChange}
                required
                placeholder="Seu email"
                disabled={loading}
              />
            </div>
            <div>
              <Label htmlFor="skills">Habilidades:</Label>
              <Input
                type="text"
                name="skills"
                value={formData.skills}
                onChange={handleChange}
                required
                placeholder="Ex: Python, Django"
                disabled={loading}
              />
            </div>
            <div>
              <h3 className="text-lg font-semibold">Experiência</h3>
              {formData.experience.map((exp, index) => (
                <div
                  key={index}
                  className="border p-4 rounded-md space-y-4 mb-4"
                >
                  <div>
                    <Label htmlFor={`position-${index}`}>Posição:</Label>
                    <Input
                      type="text"
                      name="position"
                      value={exp.position}
                      onChange={(e) => handleExperienceChange(index, e)}
                      required
                      placeholder="Cargo"
                      disabled={loading}
                    />
                  </div>
                  <div>
                    <Label htmlFor={`company-${index}`}>Empresa:</Label>
                    <Input
                      type="text"
                      name="company"
                      value={exp.company}
                      onChange={(e) => handleExperienceChange(index, e)}
                      required
                      placeholder="Empresa"
                      disabled={loading}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor={`start_year-${index}`}>
                        Ano de Início:
                      </Label>
                      <Input
                        type="number"
                        name="start_year"
                        value={exp.start_year}
                        onChange={(e) => handleExperienceChange(index, e)}
                        required
                        placeholder="Ano inicial"
                        disabled={loading}
                      />
                    </div>
                    <div>
                      <Label htmlFor={`end_year-${index}`}>
                        Ano de Término:
                      </Label>
                      <Input
                        type="number"
                        name="end_year"
                        value={exp.end_year}
                        onChange={(e) => handleExperienceChange(index, e)}
                        required
                        placeholder="Ano final"
                        disabled={loading}
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor={`description-${index}`}>Descrição:</Label>
                    <Textarea
                      name="description"
                      value={exp.description}
                      onChange={(e) => handleExperienceChange(index, e)}
                      required
                      placeholder="Descrição das responsabilidades"
                      disabled={loading}
                    />
                  </div>
                </div>
              ))}
              <Button
                type="button"
                onClick={addExperience}
                variant="secondary"
                disabled={loading}
              >
                Adicionar Experiência
              </Button>
            </div>
            <Button type="submit" variant="default" disabled={loading}>
              Gerar Currículo
            </Button>
          </form>
        </CardContent>
        <CardFooter>
          <p className="text-sm text-gray-500">
            Preencha os campos para gerar um currículo em PDF.
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}

export default App;
